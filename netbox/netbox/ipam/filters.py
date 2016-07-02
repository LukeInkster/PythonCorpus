import django_filters
from netaddr import IPNetwork
from netaddr.core import AddrFormatError

from dcim.models import Site, Device, Interface

from .models import RIR, Aggregate, VRF, Prefix, IPAddress, VLAN, Role


class VRFFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        name='name',
        lookup_type='icontains',
        label='Name',
    )

    class Meta:
        model = VRF
        fields = ['name', 'rd']


class AggregateFilter(django_filters.FilterSet):
    rir_id = django_filters.ModelMultipleChoiceFilter(
        name='rir',
        queryset=RIR.objects.all(),
        label='RIR (ID)',
    )
    rir = django_filters.ModelMultipleChoiceFilter(
        name='rir',
        queryset=RIR.objects.all(),
        to_field_name='slug',
        label='RIR (slug)',
    )

    class Meta:
        model = Aggregate
        fields = ['family', 'rir_id', 'rir', 'date_added']


class PrefixFilter(django_filters.FilterSet):
    q = django_filters.MethodFilter(
        action='search',
        label='Search',
    )
    parent = django_filters.MethodFilter(
        action='search_by_parent',
        label='Parent prefix',
    )
    vrf = django_filters.MethodFilter(
        action='_vrf',
        label='VRF',
    )
    # Duplicate of `vrf` for backward-compatibility
    vrf_id = django_filters.MethodFilter(
        action='_vrf',
        label='VRF',
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        name='site',
        queryset=Site.objects.all(),
        label='Site (ID)',
    )
    site = django_filters.ModelMultipleChoiceFilter(
        name='site',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label='Site (slug)',
    )
    vlan_id = django_filters.ModelMultipleChoiceFilter(
        name='vlan',
        queryset=VLAN.objects.all(),
        label='VLAN (ID)',
    )
    vlan_vid = django_filters.NumberFilter(
        name='vlan__vid',
        label='VLAN number (1-4095)',
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        name='role',
        queryset=Role.objects.all(),
        label='Role (ID)',
    )
    role = django_filters.ModelMultipleChoiceFilter(
        name='role',
        queryset=Role.objects.all(),
        to_field_name='slug',
        label='Role (slug)',
    )

    class Meta:
        model = Prefix
        fields = ['family', 'site_id', 'site', 'vrf', 'vrf_id', 'vlan_id', 'vlan_vid', 'status', 'role_id', 'role']

    def search(self, queryset, value):
        value = value.strip()
        try:
            query = str(IPNetwork(value).cidr)
            return queryset.filter(prefix__net_contains_or_equals=query)
        except AddrFormatError:
            return queryset.none()

    def search_by_parent(self, queryset, value):
        value = value.strip()
        if not value:
            return queryset
        try:
            query = str(IPNetwork(value).cidr)
            return queryset.filter(prefix__net_contained_or_equal=query)
        except AddrFormatError:
            return queryset.none()

    def _vrf(self, queryset, value):
        if str(value) == '':
            return queryset
        try:
            vrf_id = int(value)
        except ValueError:
            return queryset.none()
        if vrf_id == 0:
            return queryset.filter(vrf__isnull=True)
        return queryset.filter(vrf__pk=value)


class IPAddressFilter(django_filters.FilterSet):
    q = django_filters.MethodFilter(
        action='search',
        label='Search',
    )
    vrf = django_filters.MethodFilter(
        action='_vrf',
        label='VRF',
    )
    # Duplicate of `vrf` for backward-compatibility
    vrf_id = django_filters.MethodFilter(
        action='_vrf',
        label='VRF',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        name='interface__device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        name='interface__device',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device (name)',
    )
    interface_id = django_filters.ModelMultipleChoiceFilter(
        name='interface',
        queryset=Interface.objects.all(),
        label='Interface (ID)',
    )

    class Meta:
        model = IPAddress
        fields = ['q', 'family', 'vrf_id', 'vrf', 'device_id', 'device', 'interface_id']

    def search(self, queryset, value):
        value = value.strip()
        try:
            query = str(IPNetwork(value))
            return queryset.filter(address__net_host=query)
        except AddrFormatError:
            return queryset.none()

    def _vrf(self, queryset, value):
        if str(value) == '':
            return queryset
        try:
            vrf_id = int(value)
        except ValueError:
            return queryset.none()
        if vrf_id == 0:
            return queryset.filter(vrf__isnull=True)
        return queryset.filter(vrf__pk=value)


class VLANFilter(django_filters.FilterSet):
    site_id = django_filters.ModelMultipleChoiceFilter(
        name='site',
        queryset=Site.objects.all(),
        label='Site (ID)',
    )
    site = django_filters.ModelMultipleChoiceFilter(
        name='site',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label='Site (slug)',
    )
    name = django_filters.CharFilter(
        name='name',
        lookup_type='icontains',
        label='Name',
    )
    vid = django_filters.NumberFilter(
        name='vid',
        label='VLAN number (1-4095)',
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        name='role',
        queryset=Role.objects.all(),
        label='Role (ID)',
    )
    role = django_filters.ModelMultipleChoiceFilter(
        name='role',
        queryset=Role.objects.all(),
        to_field_name='slug',
        label='Role (slug)',
    )

    class Meta:
        model = VLAN
        fields = ['site_id', 'site', 'vid', 'name', 'status', 'role_id', 'role']
