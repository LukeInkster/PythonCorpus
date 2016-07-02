from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, ObjectDoesNotExist

from extras.rpc import RPC_CLIENTS
from utilities.fields import NullableCharField
from utilities.models import CreatedUpdatedModel


RACK_FACE_FRONT = 0
RACK_FACE_REAR = 1
RACK_FACE_CHOICES = [
    [RACK_FACE_FRONT, 'Front'],
    [RACK_FACE_REAR, 'Rear'],
]

COLOR_TEAL = 'teal'
COLOR_GREEN = 'green'
COLOR_BLUE = 'blue'
COLOR_PURPLE = 'purple'
COLOR_YELLOW = 'yellow'
COLOR_ORANGE = 'orange'
COLOR_RED = 'red'
COLOR_GRAY1 = 'light_gray'
COLOR_GRAY2 = 'medium_gray'
COLOR_GRAY3 = 'dark_gray'
DEVICE_ROLE_COLOR_CHOICES = [
    [COLOR_TEAL, 'Teal'],
    [COLOR_GREEN, 'Green'],
    [COLOR_BLUE, 'Blue'],
    [COLOR_PURPLE, 'Purple'],
    [COLOR_YELLOW, 'Yellow'],
    [COLOR_ORANGE, 'Orange'],
    [COLOR_RED, 'Red'],
    [COLOR_GRAY1, 'Light Gray'],
    [COLOR_GRAY2, 'Medium Gray'],
    [COLOR_GRAY3, 'Dark Gray'],
]

IFACE_FF_VIRTUAL = 0
IFACE_FF_100M_COPPER = 800
IFACE_FF_1GE_COPPER = 1000
IFACE_FF_SFP = 1100
IFACE_FF_10GE_COPPER = 1150
IFACE_FF_SFP_PLUS = 1200
IFACE_FF_XFP = 1300
IFACE_FF_QSFP_PLUS = 1400
IFACE_FF_CHOICES = [
    [IFACE_FF_VIRTUAL, 'Virtual'],
    [IFACE_FF_100M_COPPER, '10/100M (100BASE-TX)'],
    [IFACE_FF_1GE_COPPER, '1GE (1000BASE-T)'],
    [IFACE_FF_SFP, '1GE (SFP)'],
    [IFACE_FF_10GE_COPPER, '10GE (10GBASE-T)'],
    [IFACE_FF_SFP_PLUS, '10GE (SFP+)'],
    [IFACE_FF_XFP, '10GE (XFP)'],
    [IFACE_FF_QSFP_PLUS, '40GE (QSFP+)'],
]

STATUS_ACTIVE = True
STATUS_OFFLINE = False
STATUS_CHOICES = [
    [STATUS_ACTIVE, 'Active'],
    [STATUS_OFFLINE, 'Offline'],
]

CONNECTION_STATUS_PLANNED = False
CONNECTION_STATUS_CONNECTED = True
CONNECTION_STATUS_CHOICES = [
    [CONNECTION_STATUS_PLANNED, 'Planned'],
    [CONNECTION_STATUS_CONNECTED, 'Connected'],
]

# For mapping platform -> NC client
RPC_CLIENT_JUNIPER_JUNOS = 'juniper-junos'
RPC_CLIENT_CISCO_IOS = 'cisco-ios'
RPC_CLIENT_OPENGEAR = 'opengear'
RPC_CLIENT_CHOICES = [
    [RPC_CLIENT_JUNIPER_JUNOS, 'Juniper Junos (NETCONF)'],
    [RPC_CLIENT_CISCO_IOS, 'Cisco IOS (SSH)'],
    [RPC_CLIENT_OPENGEAR, 'Opengear (SSH)'],
]


def order_interfaces(queryset, sql_col, primary_ordering=tuple()):
    """
    Attempt to match interface names by their slot/position identifiers and order according. Matching is done using the
    following pattern:

        {a}/{b}/{c}:{d}

    Interfaces are ordered first by field a, then b, then c, and finally d. Leading text (which typically indicates the
    interface's type) is ignored. If any fields are not contained by an interface name, those fields are treated as
    None. 'None' is ordered after all other values. For example:

        et-0/0/0
        et-0/0/1
        et-0/1/0
        xe-0/1/1:0
        xe-0/1/1:1
        xe-0/1/1:2
        xe-0/1/1:3
        et-0/1/2
        ...
        et-0/1/9
        et-0/1/10
        et-0/1/11
        et-1/0/0
        et-1/0/1
        ...
        vlan1
        vlan10

    :param queryset: The base queryset to be ordered
    :param sql_col: Table and name of the SQL column which contains the interface name (ex: ''dcim_interface.name')
    :param primary_ordering: A tuple of fields which take ordering precedence before the interface name (optional)
    """
    ordering = primary_ordering + ('_id1', '_id2', '_id3', '_id4')
    return queryset.extra(select={
        '_id1': "CAST(SUBSTRING({} FROM '([0-9]+)\/[0-9]+\/[0-9]+(:[0-9]+)?$') AS integer)".format(sql_col),
        '_id2': "CAST(SUBSTRING({} FROM '([0-9]+)\/[0-9]+(:[0-9]+)?$') AS integer)".format(sql_col),
        '_id3': "CAST(SUBSTRING({} FROM '([0-9]+)(:[0-9]+)?$') AS integer)".format(sql_col),
        '_id4': "CAST(SUBSTRING({} FROM ':([0-9]+)$') AS integer)".format(sql_col),
    }).order_by(*ordering)


class Site(CreatedUpdatedModel):
    """
    A Site represents a geographic location within a network; typically a building or campus. The optional facility
    field can be used to include an external designation, such as a data center name (e.g. Equinix SV6).
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    facility = models.CharField(max_length=50, blank=True)
    asn = models.PositiveIntegerField(blank=True, null=True, verbose_name='ASN')
    physical_address = models.CharField(max_length=200, blank=True)
    shipping_address = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:site', args=[self.slug])

    def to_csv(self):
        return ','.join([
            self.name,
            self.slug,
            self.facility,
            str(self.asn),
        ])

    @property
    def count_prefixes(self):
        return self.prefixes.count()

    @property
    def count_vlans(self):
        return self.vlans.count()

    @property
    def count_racks(self):
        return Rack.objects.filter(site=self).count()

    @property
    def count_devices(self):
        return Device.objects.filter(rack__site=self).count()

    @property
    def count_circuits(self):
        return self.circuits.count()


class RackGroup(models.Model):
    """
    Racks can be grouped as subsets within a Site. The scope of a group will depend on how Sites are defined. For
    example, if a Site spans a corporate campus, a RackGroup might be defined to represent each building within that
    campus. If a Site instead represents a single building, a RackGroup might represent a single room or floor.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    site = models.ForeignKey('Site', related_name='rack_groups')

    class Meta:
        ordering = ['site', 'name']
        unique_together = [
            ['site', 'name'],
            ['site', 'slug'],
        ]

    def __unicode__(self):
        return '{} - {}'.format(self.site.name, self.name)

    def get_absolute_url(self):
        return "{}?group_id={}".format(reverse('dcim:rack_list'), self.pk)


class Rack(CreatedUpdatedModel):
    """
    Devices are housed within Racks. Each rack has a defined height measured in rack units, and a front and rear face.
    Each Rack is assigned to a Site and (optionally) a RackGroup.
    """
    name = models.CharField(max_length=50)
    facility_id = NullableCharField(max_length=30, blank=True, null=True, verbose_name='Facility ID')
    site = models.ForeignKey('Site', related_name='racks', on_delete=models.PROTECT)
    group = models.ForeignKey('RackGroup', related_name='racks', blank=True, null=True, on_delete=models.SET_NULL)
    u_height = models.PositiveSmallIntegerField(default=42, verbose_name='Height (U)')
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['site', 'name']
        unique_together = [
            ['site', 'name'],
            ['site', 'facility_id'],
        ]

    def __unicode__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse('dcim:rack', args=[self.pk])

    def clean(self):

        # Validate that Rack is tall enough to house the installed Devices
        if self.pk:
            top_device = Device.objects.filter(rack=self).exclude(position__isnull=True).order_by('-position').first()
            if top_device:
                min_height = top_device.position + top_device.device_type.u_height - 1
                if self.u_height < min_height:
                    raise ValidationError("Rack must be at least {}U tall with currently installed devices."
                                          .format(min_height))

    def to_csv(self):
        return ','.join([
            self.site.name,
            self.group.name if self.group else '',
            self.name,
            self.facility_id or '',
            str(self.u_height),
        ])

    @property
    def units(self):
        return reversed(range(1, self.u_height + 1))

    @property
    def display_name(self):
        if self.facility_id:
            return "{} ({})".format(self.name, self.facility_id)
        return self.name

    def get_rack_units(self, face=RACK_FACE_FRONT, exclude=None, remove_redundant=False):
        """
        Return a list of rack units as dictionaries. Example: {'device': None, 'face': 0, 'id': 48, 'name': 'U48'}
        Each key 'device' is either a Device or None. By default, multi-U devices are repeated for each U they occupy.

        :param face: Rack face (front or rear)
        :param exclude: PK of a Device to exclude (optional); helpful when relocating a Device within a Rack
        :param remove_redundant: If True, rack units occupied by a device already listed will be omitted
        """

        elevation = OrderedDict()
        for u in reversed(range(1, self.u_height + 1)):
            elevation[u] = {'id': u, 'name': 'U{}'.format(u), 'face': face, 'device': None}

        # Add devices to rack units list
        if self.pk:
            for device in Device.objects.select_related('device_type__manufacturer', 'device_role')\
                    .exclude(pk=exclude)\
                    .filter(rack=self, position__gt=0)\
                    .filter(Q(face=face) | Q(device_type__is_full_depth=True)):
                if remove_redundant:
                    elevation[device.position]['device'] = device
                    for u in range(device.position + 1, device.position + device.device_type.u_height):
                        elevation.pop(u, None)
                else:
                    for u in range(device.position, device.position + device.device_type.u_height):
                        elevation[u]['device'] = device

        return [u for u in elevation.values()]

    def get_front_elevation(self):
        return self.get_rack_units(face=RACK_FACE_FRONT, remove_redundant=True)

    def get_rear_elevation(self):
        return self.get_rack_units(face=RACK_FACE_REAR, remove_redundant=True)

    def get_available_units(self, u_height=1, rack_face=None, exclude=list()):
        """
        Return a list of units within the rack available to accommodate a device of a given U height (default 1).
        Optionally exclude one or more devices when calculating empty units (needed when moving a device from one
        position to another within a rack).

        :param u_height: Minimum number of contiguous free units required
        :param rack_face: The face of the rack (front or rear) required; 'None' if device is full depth
        :param exclude: List of devices IDs to exclude (useful when moving a device within a rack)
        """

        # Gather all devices which consume U space within the rack
        devices = self.devices.select_related().filter(position__gte=1).exclude(pk__in=exclude)

        # Initialize the rack unit skeleton
        units = range(1, self.u_height + 1)

        # Remove units consumed by installed devices
        for d in devices:
            if rack_face is None or d.face == rack_face or d.device_type.is_full_depth:
                for u in range(d.position, d.position + d.device_type.u_height):
                    try:
                        units.remove(u)
                    except ValueError:
                        # Found overlapping devices in the rack!
                        pass

        # Remove units without enough space above them to accommodate a device of the specified height
        available_units = []
        for u in units:
            if set(range(u, u + u_height)).issubset(units):
                available_units.append(u)

        return list(reversed(available_units))

    def get_0u_devices(self):
        return self.devices.filter(position=0)


#
# Device Types
#

class Manufacturer(models.Model):
    """
    A Manufacturer represents a company which produces hardware devices; for example, Juniper or Dell.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?manufacturer={}".format(reverse('dcim:devicetype_list'), self.slug)


class DeviceType(models.Model):
    """
    A DeviceType represents a particular make (Manufacturer) and model of device. It specifies rack height and depth, as
    well as high-level functional role(s).

    Each DeviceType can have an arbitrary number of component templates assigned to it, which define console, power, and
    interface objects. For example, a Juniper EX4300-48T DeviceType would have:

      * 1 ConsolePortTemplate
      * 2 PowerPortTemplates
      * 48 InterfaceTemplates

    When a new Device of this type is created, the appropriate console, power, and interface objects (as defined by the
    DeviceType) are automatically created as well.
    """
    manufacturer = models.ForeignKey('Manufacturer', related_name='device_types', on_delete=models.PROTECT)
    model = models.CharField(max_length=50)
    slug = models.SlugField()
    u_height = models.PositiveSmallIntegerField(verbose_name='Height (U)', default=1)
    is_full_depth = models.BooleanField(default=True, verbose_name="Is full depth",
                                        help_text="Device consumes both front and rear rack faces")
    is_console_server = models.BooleanField(default=False, verbose_name='Is a console server',
                                            help_text="This type of device has console server ports")
    is_pdu = models.BooleanField(default=False, verbose_name='Is a PDU',
                                 help_text="This type of device has power outlets")
    is_network_device = models.BooleanField(default=True, verbose_name='Is a network device',
                                            help_text="This type of device has network interfaces")

    class Meta:
        ordering = ['manufacturer', 'model']
        unique_together = [
            ['manufacturer', 'model'],
            ['manufacturer', 'slug'],
        ]

    def __unicode__(self):
        return "{0} {1}".format(self.manufacturer, self.model)

    def get_absolute_url(self):
        return reverse('dcim:devicetype', args=[self.pk])


class ConsolePortTemplate(models.Model):
    """
    A template for a ConsolePort to be created for a new Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='console_port_templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['device_type', 'name']
        unique_together = ['device_type', 'name']

    def __unicode__(self):
        return self.name


class ConsoleServerPortTemplate(models.Model):
    """
    A template for a ConsoleServerPort to be created for a new Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='cs_port_templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['device_type', 'name']
        unique_together = ['device_type', 'name']

    def __unicode__(self):
        return self.name


class PowerPortTemplate(models.Model):
    """
    A template for a PowerPort to be created for a new Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='power_port_templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['device_type', 'name']
        unique_together = ['device_type', 'name']

    def __unicode__(self):
        return self.name


class PowerOutletTemplate(models.Model):
    """
    A template for a PowerOutlet to be created for a new Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='power_outlet_templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['device_type', 'name']
        unique_together = ['device_type', 'name']

    def __unicode__(self):
        return self.name


class InterfaceTemplateManager(models.Manager):

    def get_queryset(self):
        qs = super(InterfaceTemplateManager, self).get_queryset()
        return order_interfaces(qs, 'dcim_interfacetemplate.name', ('device_type',))


class InterfaceTemplate(models.Model):
    """
    A template for a physical data interface on a new Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='interface_templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    form_factor = models.PositiveSmallIntegerField(choices=IFACE_FF_CHOICES, default=IFACE_FF_SFP_PLUS)
    mgmt_only = models.BooleanField(default=False, verbose_name='Management only')

    objects = InterfaceTemplateManager()

    class Meta:
        ordering = ['device_type', 'name']
        unique_together = ['device_type', 'name']

    def __unicode__(self):
        return self.name


#
# Devices
#

class DeviceRole(models.Model):
    """
    Devices are organized by functional role; for example, "Core Switch" or "File Server". Each DeviceRole is assigned a
    color to be used when displaying rack elevations.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=30, choices=DEVICE_ROLE_COLOR_CHOICES)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?role={}".format(reverse('dcim:device_list'), self.slug)


class Platform(models.Model):
    """
    Platform refers to the software or firmware running on a Device; for example, "Cisco IOS-XR" or "Juniper Junos".
    NetBox uses Platforms to determine how to interact with devices when pulling inventory data or other information by
    specifying an remote procedure call (RPC) client.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    rpc_client = models.CharField(max_length=30, choices=RPC_CLIENT_CHOICES, blank=True, verbose_name='RPC client')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?platform={}".format(reverse('dcim:device_list'), self.slug)


class Device(CreatedUpdatedModel):
    """
    A Device represents a piece of physical hardware mounted within a Rack. Each Device is assigned a DeviceType,
    DeviceRole, and (optionally) a Platform. Device names are not required, however if one is set it must be unique.

    Each Device must be assigned to a Rack, although associating it with a particular rack face or unit is optional (for
    example, vertically mounted PDUs do not consume rack units).

    When a new Device is created, console/power/interface components are created along with it as dictated by the
    component templates assigned to its DeviceType. Components can also be added, modified, or deleted after the
    creation of a Device.
    """
    device_type = models.ForeignKey('DeviceType', related_name='instances', on_delete=models.PROTECT)
    device_role = models.ForeignKey('DeviceRole', related_name='devices', on_delete=models.PROTECT)
    platform = models.ForeignKey('Platform', related_name='devices', blank=True, null=True, on_delete=models.SET_NULL)
    name = NullableCharField(max_length=50, blank=True, null=True, unique=True)
    serial = models.CharField(max_length=50, blank=True, verbose_name='Serial number')
    rack = models.ForeignKey('Rack', related_name='devices', on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1)],
                                                verbose_name='Position (U)',
                                                help_text='Number of the lowest U position occupied by the device')
    face = models.PositiveSmallIntegerField(blank=True, null=True, choices=RACK_FACE_CHOICES, verbose_name='Rack face')
    status = models.BooleanField(choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name='Status')
    primary_ip = models.OneToOneField('ipam.IPAddress', related_name='primary_for', on_delete=models.SET_NULL,
                                      blank=True, null=True, verbose_name='Primary IP')
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        unique_together = ['rack', 'position', 'face']

    def __unicode__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse('dcim:device', args=[self.pk])

    def clean(self):

        # Validate position/face combination
        if self.position and self.face is None:
            raise ValidationError("Must specify rack face with rack position.")

        # Validate rack space
        try:
            rack_face = self.face if not self.device_type.is_full_depth else None
        except DeviceType.DoesNotExist:
            raise ValidationError("Must specify device type.")
        exclude_list = [self.pk] if self.pk else []
        try:
            available_units = self.rack.get_available_units(u_height=self.device_type.u_height, rack_face=rack_face,
                                                            exclude=exclude_list)
            if self.position and self.position not in available_units:
                raise ValidationError("U{} is already occupied or does not have sufficient space to accommodate a(n) "
                                      "{} ({}U).".format(self.position, self.device_type, self.device_type.u_height))
        except Rack.DoesNotExist:
            pass

    def save(self, *args, **kwargs):

        is_new = not bool(self.pk)

        super(Device, self).save(*args, **kwargs)

        # If this is a new Device, instantiate all of the related components per the DeviceType definition
        if is_new:
            ConsolePort.objects.bulk_create(
                [ConsolePort(device=self, name=template.name) for template in
                 self.device_type.console_port_templates.all()]
            )
            ConsoleServerPort.objects.bulk_create(
                [ConsoleServerPort(device=self, name=template.name) for template in
                 self.device_type.cs_port_templates.all()]
            )
            PowerPort.objects.bulk_create(
                [PowerPort(device=self, name=template.name) for template in
                 self.device_type.power_port_templates.all()]
            )
            PowerOutlet.objects.bulk_create(
                [PowerOutlet(device=self, name=template.name) for template in
                 self.device_type.power_outlet_templates.all()]
            )
            Interface.objects.bulk_create(
                [Interface(device=self, name=template.name, form_factor=template.form_factor,
                           mgmt_only=template.mgmt_only) for template in self.device_type.interface_templates.all()]
            )

    def to_csv(self):
        return ','.join([
            self.name or '',
            self.device_role.name,
            self.device_type.manufacturer.name,
            self.device_type.model,
            self.platform.name if self.platform else '',
            self.serial,
            self.rack.site.name,
            self.rack.name,
            str(self.position) if self.position else '',
            self.get_face_display() or '',
        ])

    @property
    def display_name(self):
        if self.name:
            return self.name
        elif self.position:
            return "{} ({} U{})".format(self.device_type, self.rack.name, self.position)
        else:
            return "{} ({})".format(self.device_type, self.rack.name)

    @property
    def identifier(self):
        """
        Return the device name if set; otherwise return the Device's primary key as {pk}
        """
        if self.name is not None:
            return self.name
        return '{{{}}}'.format(self.pk)

    def get_rpc_client(self):
        """
        Return the appropriate RPC (e.g. NETCONF, ssh, etc.) client for this device's platform, if one is defined.
        """
        if not self.platform:
            return None
        return RPC_CLIENTS.get(self.platform.rpc_client)


class ConsolePort(models.Model):
    """
    A physical console port within a Device. ConsolePorts connect to ConsoleServerPorts.
    """
    device = models.ForeignKey('Device', related_name='console_ports', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    cs_port = models.OneToOneField('ConsoleServerPort', related_name='connected_console', on_delete=models.SET_NULL,
                                   verbose_name='Console server port', blank=True, null=True)
    connection_status = models.NullBooleanField(choices=CONNECTION_STATUS_CHOICES, default=CONNECTION_STATUS_CONNECTED)

    class Meta:
        ordering = ['device', 'name']
        unique_together = ['device', 'name']

    def __unicode__(self):
        return self.name

    # Used for connections export
    def to_csv(self):
        return ','.join([
            self.cs_port.device.identifier if self.cs_port else '',
            self.cs_port.name if self.cs_port else '',
            self.device.identifier,
            self.name,
            self.get_connection_status_display(),
        ])


class ConsoleServerPortManager(models.Manager):

    def get_queryset(self):
        """
        Include the trailing numeric portion of each port name to allow for proper ordering.
        For example:
            Port 1, Port 2, Port 3 ... Port 9, Port 10, Port 11 ...
        Instead of:
            Port 1, Port 10, Port 11 ... Port 19, Port 2, Port 20 ...
        """
        return super(ConsoleServerPortManager, self).get_queryset().extra(select={
            'name_as_integer': "CAST(substring(dcim_consoleserverport.name FROM '[0-9]+$') AS INTEGER)",
        }).order_by('device', 'name_as_integer')


class ConsoleServerPort(models.Model):
    """
    A physical port within a Device (typically a designated console server) which provides access to ConsolePorts.
    """
    device = models.ForeignKey('Device', related_name='cs_ports', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    objects = ConsoleServerPortManager()

    class Meta:
        unique_together = ['device', 'name']

    def __unicode__(self):
        return self.name


class PowerPort(models.Model):
    """
    A physical power supply (intake) port within a Device. PowerPorts connect to PowerOutlets.
    """
    device = models.ForeignKey('Device', related_name='power_ports', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    power_outlet = models.OneToOneField('PowerOutlet', related_name='connected_port', on_delete=models.SET_NULL,
                                        blank=True, null=True)
    connection_status = models.NullBooleanField(choices=CONNECTION_STATUS_CHOICES, default=CONNECTION_STATUS_CONNECTED)

    class Meta:
        ordering = ['device', 'name']
        unique_together = ['device', 'name']

    def __unicode__(self):
        return self.name

    # Used for connections export
    def to_csv(self):
        return ','.join([
            self.power_outlet.device.identifier if self.power_outlet else '',
            self.power_outlet.name if self.power_outlet else '',
            self.device.identifier,
            self.name,
            self.get_connection_status_display(),
        ])


class PowerOutletManager(models.Manager):

    def get_queryset(self):
        return super(PowerOutletManager, self).get_queryset().extra(select={
            'name_padded': "CONCAT(SUBSTRING(dcim_poweroutlet.name FROM '^[^0-9]+'), "
                           "LPAD(SUBSTRING(dcim_poweroutlet.name FROM '[0-9\/]+$'), 8, '0'))",
        }).order_by('device', 'name_padded')


class PowerOutlet(models.Model):
    """
    A physical power outlet (output) within a Device which provides power to a PowerPort.
    """
    device = models.ForeignKey('Device', related_name='power_outlets', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    objects = PowerOutletManager()

    class Meta:
        unique_together = ['device', 'name']

    def __unicode__(self):
        return self.name


class InterfaceManager(models.Manager):

    def get_queryset(self):
        qs = super(InterfaceManager, self).get_queryset()
        return order_interfaces(qs, 'dcim_interface.name', ('device',))

    def virtual(self):
        return self.get_queryset().filter(form_factor=IFACE_FF_VIRTUAL)

    def physical(self):
        return self.get_queryset().exclude(form_factor=IFACE_FF_VIRTUAL)


class Interface(models.Model):
    """
    A physical data interface within a Device. An Interface can connect to exactly one other Interface via the creation
    of an InterfaceConnection.
    """
    device = models.ForeignKey('Device', related_name='interfaces', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    form_factor = models.PositiveSmallIntegerField(choices=IFACE_FF_CHOICES, default=IFACE_FF_SFP_PLUS)
    mgmt_only = models.BooleanField(default=False, verbose_name='OOB Management',
                                    help_text="This interface is used only for out-of-band management")
    description = models.CharField(max_length=100, blank=True)

    objects = InterfaceManager()

    class Meta:
        ordering = ['device', 'name']
        unique_together = ['device', 'name']

    def __unicode__(self):
        return self.name

    @property
    def is_physical(self):
        return self.form_factor != IFACE_FF_VIRTUAL

    @property
    def is_connected(self):
        try:
            return bool(self.circuit)
        except ObjectDoesNotExist:
            pass
        return bool(self.connection)

    @property
    def connection(self):
        try:
            return self.connected_as_a
        except ObjectDoesNotExist:
            pass
        try:
            return self.connected_as_b
        except ObjectDoesNotExist:
            pass
        return None

    def get_connected_interface(self):
        try:
            connection = InterfaceConnection.objects.select_related().get(Q(interface_a=self) | Q(interface_b=self))
            if connection.interface_a == self:
                return connection.interface_b
            else:
                return connection.interface_a
        except InterfaceConnection.DoesNotExist:
            return None
        except InterfaceConnection.MultipleObjectsReturned as e:
            raise e("Multiple connections found for {0} interface {1}!".format(self.device, self))


class InterfaceConnection(models.Model):
    """
    An InterfaceConnection represents a symmetrical, one-to-one connection between two Interfaces. There is no
    significant difference between the interface_a and interface_b fields.
    """
    interface_a = models.OneToOneField('Interface', related_name='connected_as_a', on_delete=models.CASCADE)
    interface_b = models.OneToOneField('Interface', related_name='connected_as_b', on_delete=models.CASCADE)
    connection_status = models.BooleanField(choices=CONNECTION_STATUS_CHOICES, default=CONNECTION_STATUS_CONNECTED,
                                            verbose_name='Status')

    def clean(self):
        if self.interface_a == self.interface_b:
            raise ValidationError("Cannot connect an interface to itself")

    # Used for connections export
    def to_csv(self):
        return ','.join([
            self.interface_a.device.identifier,
            self.interface_a.name,
            self.interface_b.device.identifier,
            self.interface_b.name,
            self.get_connection_status_display(),
        ])


class Module(models.Model):
    """
    A Module represents a piece of hardware within a Device, such as a line card or power supply. Modules are used only
    for inventory purposes.
    """
    device = models.ForeignKey('Device', related_name='modules', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='submodules', blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name='Name')
    part_id = models.CharField(max_length=50, verbose_name='Part ID', blank=True)
    serial = models.CharField(max_length=50, verbose_name='Serial number', blank=True)
    discovered = models.BooleanField(default=False, verbose_name='Discovered')

    class Meta:
        ordering = ['device__id', 'parent__id', 'name']
        unique_together = ['device', 'parent', 'name']

    def __unicode__(self):
        return self.name
