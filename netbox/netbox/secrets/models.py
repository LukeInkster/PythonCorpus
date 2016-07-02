import os
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import force_bytes

from dcim.models import Device
from utilities.models import CreatedUpdatedModel

from .hashers import SecretValidationHasher


def generate_master_key():
    """
    Generate a new 256-bit (32 bytes) AES key to be used for symmetric encryption of secrets.
    """
    return os.urandom(32)


def encrypt_master_key(master_key, public_key):
    """
    Encrypt a secret key with the provided public RSA key.
    """
    key = RSA.importKey(public_key)
    cipher = PKCS1_OAEP.new(key)
    return cipher.encrypt(master_key)


def decrypt_master_key(master_key_cipher, private_key):
    """
    Decrypt a secret key with the provided private RSA key.
    """
    key = RSA.importKey(private_key)
    cipher = PKCS1_OAEP.new(key)
    return cipher.decrypt(master_key_cipher)


class UserKeyQuerySet(models.QuerySet):

    def active(self):
        return self.filter(master_key_cipher__isnull=False)

    def delete(self):
        # Disable bulk deletion to avoid accidentally wiping out all copies of the master key.
        raise Exception("Bulk deletion has been disabled.")


class UserKey(CreatedUpdatedModel):
    """
    A UserKey stores a user's personal RSA (public) encryption key, which is used to generate their unique encrypted
    copy of the master encryption key. The encrypted instance of the master key can be decrypted only with the user's
    matching (private) decryption key.
    """
    user = models.OneToOneField(User, related_name='user_key', verbose_name='User')
    public_key = models.TextField(verbose_name='RSA public key')
    master_key_cipher = models.BinaryField(max_length=512, blank=True, null=True, editable=False)

    objects = UserKeyQuerySet.as_manager()

    class Meta:
        ordering = ['user__username']
        permissions = (
            ('activate_userkey', "Can activate user keys for decryption"),
        )

    def __init__(self, *args, **kwargs):
        super(UserKey, self).__init__(*args, **kwargs)

        # Store the initial public_key and master_key_cipher to check for changes on save().
        self.__initial_public_key = self.public_key
        self.__initial_master_key_cipher = self.master_key_cipher

    def __unicode__(self):
        return self.user.username

    def clean(self, *args, **kwargs):

        # Validate the public key format and length.
        if self.public_key:
            try:
                pubkey = RSA.importKey(self.public_key)
            except ValueError:
                raise ValidationError("Invalid RSA key format.")
            except:
                raise ValidationError("Something went wrong while trying to save your key. Please ensure that you're "
                                      "uploading a valid RSA public key in PEM format (no SSH/PGP).")
            # key.size() returns 1 less than the key modulus
            pubkey_length = pubkey.size() + 1
            if pubkey_length < settings.SECRETS_MIN_PUBKEY_SIZE:
                raise ValidationError("Insufficient key length. Keys must be at least {} bits long."
                                      .format(settings.SECRETS_MIN_PUBKEY_SIZE))
            # We can't use keys bigger than our master_key_cipher field can hold
            if pubkey_length > 4096:
                raise ValidationError("Public key size ({}) is too large. Maximum key size is 4096 bits."
                                      .format(pubkey_length))

        super(UserKey, self).clean()

    def save(self, *args, **kwargs):

        # Check whether public_key has been modified. If so, nullify the initial master_key_cipher.
        if self.__initial_master_key_cipher and self.public_key != self.__initial_public_key:
            self.master_key_cipher = None

        # If no other active UserKeys exist, generate a new master key and use it to activate this UserKey.
        if self.is_filled() and not self.is_active() and not UserKey.objects.active().count():
            master_key = generate_master_key()
            self.master_key_cipher = encrypt_master_key(master_key, self.public_key)

        super(UserKey, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):

        # If Secrets exist and this is the last active UserKey, prevent its deletion. Deleting the last UserKey will
        # result in the master key being destroyed and rendering all Secrets inaccessible.
        if Secret.objects.count() and [uk.pk for uk in UserKey.objects.active()] == [self.pk]:
            raise Exception("Cannot delete the last active UserKey when Secrets exist! This would render all secrets "
                            "inaccessible.")

        super(UserKey, self).delete(*args, **kwargs)

    def is_filled(self):
        """
        Returns True if the UserKey has been filled with a public RSA key.
        """
        return bool(self.public_key)
    is_filled.boolean = True

    def is_active(self):
        """
        Returns True if the UserKey has been populated with an encrypted copy of the master key.
        """
        return self.master_key_cipher is not None
    is_active.boolean = True

    def get_master_key(self, private_key):
        """
        Given the User's private key, return the encrypted master key.
        """
        if not self.is_active:
            raise ValueError("Unable to retrieve master key: UserKey is inactive.")
        try:
            return decrypt_master_key(force_bytes(self.master_key_cipher), private_key)
        except ValueError:
            return None

    def activate(self, master_key):
        """
        Activate the UserKey by saving an encrypted copy of the master key to the database.
        """
        if not self.public_key:
            raise Exception("Cannot activate UserKey: Its public key must be filled first.")
        self.master_key_cipher = encrypt_master_key(master_key, self.public_key)
        self.save()


class SecretRole(models.Model):
    """
    A SecretRole represents an arbitrary functional classification of Secrets. For example, a user might define roles
    such as "Login Credentials" or "SNMP Communities."

    By default, only superusers will have access to decrypt Secrets. To allow other users to decrypt Secrets, grant them
    access to the appropriate SecretRoles either individually or by group.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    users = models.ManyToManyField(User, related_name='secretroles', blank=True)
    groups = models.ManyToManyField(Group, related_name='secretroles', blank=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?role={}".format(reverse('secrets:secret_list'), self.slug)


class Secret(CreatedUpdatedModel):
    """
    A Secret stores an AES256-encrypted copy of sensitive data, such as passwords or secret keys. An irreversible
    SHA-256 hash is stored along with the ciphertext for validation upon decryption. Each Secret is assigned to a
    Device; Devices may have multiple Secrets associated with them. A name can optionally be defined along with the
    ciphertext; this string is stored as plain text in the database.

    A Secret can be up to 65,536 bytes (64KB) in length. Each secret string will be padded with random data to a minimum
    of 64 bytes during encryption in order to protect short strings from ciphertext analysis.
    """
    device = models.ForeignKey(Device, related_name='secrets')
    role = models.ForeignKey('SecretRole', related_name='secrets', on_delete=models.PROTECT)
    name = models.CharField(max_length=100, blank=True)
    ciphertext = models.BinaryField(editable=False, max_length=65568)  # 16B IV + 2B pad length + {62-65550}B padded
    hash = models.CharField(max_length=128, editable=False)

    plaintext = None

    class Meta:
        ordering = ['device', 'role', 'name']
        unique_together = ['device', 'role', 'name']

    def __init__(self, *args, **kwargs):
        self.plaintext = kwargs.pop('plaintext', None)
        super(Secret, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.role and self.device:
            return "{} for {}".format(self.role, self.device)
        return "Secret"

    def get_absolute_url(self):
        return reverse('secrets:secret', args=[self.pk])

    def _pad(self, s):
        """
        Prepend the length of the plaintext (2B) and pad with garbage to a multiple of 16B (minimum of 64B).
        +--+--------+-------------------------------------------+
        |LL|MySecret|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx|
        +--+--------+-------------------------------------------+
        """
        if len(s) > 65535:
            raise ValueError("Maximum plaintext size is 65535 bytes.")
        # Minimum ciphertext size is 64 bytes to conceal the length of short secrets.
        if len(s) <= 62:
            pad_length = 62 - len(s)
        elif (len(s) + 2) % 16:
            pad_length = 16 - ((len(s) + 2) % 16)
        else:
            pad_length = 0
        return (
            chr(len(s) >> 8).encode() +
            chr(len(s) % 256).encode() +
            s.encode() +
            os.urandom(pad_length)
        )

    def _unpad(self, s):
        """
        Consume the first two bytes of s as a plaintext length indicator and return only that many bytes as the
        plaintext.
        """
        if isinstance(s[0], int):
            plaintext_length = (s[0] << 8) + s[1]
        elif isinstance(s[0], str):
            plaintext_length = (ord(s[0]) << 8) + ord(s[1])
        return s[2:plaintext_length + 2].decode()

    def encrypt(self, secret_key):
        """
        Generate a random initialization vector (IV) for AES. Pad the plaintext to the AES block size (16 bytes) and
        encrypt. Prepend the IV for use in decryption. Finally, record the SHA256 hash of the plaintext for validation
        upon decryption.
        """
        if self.plaintext is None:
            raise Exception("Must unlock or set plaintext before locking.")

        # Pad and encrypt plaintext
        iv = os.urandom(16)
        aes = AES.new(secret_key, AES.MODE_CFB, iv)
        self.ciphertext = iv + aes.encrypt(self._pad(self.plaintext))

        # Generate SHA256 using Django's built-in password hashing mechanism
        self.hash = make_password(self.plaintext, hasher=SecretValidationHasher())

        self.plaintext = None

    def decrypt(self, secret_key):
        """
        Consume the first 16 bytes of self.ciphertext as the AES initialization vector (IV). The remainder is decrypted
        using the IV and the provided secret key. Padding is then removed to reveal the plaintext. Finally, validate the
        decrypted plaintext value against the stored hash.
        """
        if self.plaintext is not None:
            return
        if not self.ciphertext:
            raise Exception("Must define ciphertext before unlocking.")

        # Decrypt ciphertext and remove padding
        iv = self.ciphertext[0:16]
        aes = AES.new(secret_key, AES.MODE_CFB, iv)
        plaintext = self._unpad(aes.decrypt(self.ciphertext[16:]))

        # Verify decrypted plaintext against hash
        if not self.validate(plaintext):
            raise ValueError("Invalid key or ciphertext!")

        self.plaintext = plaintext

    def validate(self, plaintext):
        """
        Validate that a given plaintext matches the stored hash.
        """
        if not self.hash:
            raise Exception("Hash has not been generated for this secret.")
        return check_password(plaintext, self.hash, preferred=SecretValidationHasher())

    def decryptable_by(self, user):
        """
        Check whether the given user has permission to decrypt this Secret.
        """
        return user in self.role.users.all() or user.groups.filter(pk__in=self.role.groups.all()).exists()
