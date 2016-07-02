from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm

from utilities.forms import BootstrapMixin


class LoginForm(AuthenticationForm, BootstrapMixin):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = ''
        self.fields['password'].widget.attrs['placeholder'] = ''


class PasswordChangeForm(DjangoPasswordChangeForm, BootstrapMixin):
    pass
