import re

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count, ProtectedError
from django.forms import ModelMultipleChoiceField, MultipleHiddenInput
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlencode
from django.views.generic import View

from ipam.models import Prefix, IPAddress, VLAN
from circuits.models import Circuit
from extras.models import TopologyMap
from utilities.error_handlers import handle_protectederror
from utilities.forms import ConfirmationForm
from utilities.views import (
    BulkDeleteView, BulkEditView, BulkImportView, ObjectDeleteView, ObjectEditView, ObjectListView,
)

from . import filters, forms, tables
from .models import (
    CONNECTION_STATUS_CONNECTED, ConsolePort, ConsolePortTemplate, ConsoleServerPort, ConsoleServerPortTemplate, Device,
    DeviceRole, DeviceType, Interface, InterfaceConnection, InterfaceTemplate, Manufacturer, Module, Platform,
    PowerOutlet, PowerOutletTemplate, PowerPort, PowerPortTemplate, Rack, RackGroup, Site,
)


EXPANSION_PATTERN = '\[(\d+-\d+)\]'


def xstr(s):
    """
    Replace None with an empty string (for CSV export)
    """
    return '' if s is None else str(s)


def expand_pattern(string):
    """
    Expand a numeric pattern into a list of strings. Examples:
      'ge-0/0/[0-3]' => ['ge-0/0/0', 'ge-0/0/1', 'ge-0/0/2', 'ge-0/0/3']
      'xe-0/[0-3]/[0-7]' => ['xe-0/0/0', 'xe-0/0/1', 'xe-0/0/2', ... 'xe-0/3/5', 'xe-0/3/6', 'xe-0/3/7']
    """
    lead, pattern, remnant = re.split(EXPANSION_PATTERN, string, maxsplit=1)
    x, y = pattern.split('-')
    for i in range(int(x), int(y) + 1):
        if remnant:
            for string in expand_pattern(remnant):
                yield "{0}{1}{2}".format(lead, i, string)
        else:
            yield "{0}{1}".format(lead, i)


#
# Sites
#

class SiteListView(ObjectListView):
    queryset = Site.objects.all()
    filter = filters.SiteFilter
    table = tables.SiteTable
    template_name = 'dcim/site_list.html'


def site(request, slug):

    site = get_object_or_404(Site, slug=slug)
    stats = {
        'rack_count': Rack.objects.filter(site=site).count(),
        'device_count': Device.objects.filter(rack__site=site).count(),
        'prefix_count': Prefix.objects.filter(site=site).count(),
        'vlan_count': VLAN.objects.filter(site=site).count(),
        'circuit_count': Circuit.objects.filter(site=site).count(),
    }
    rack_groups = RackGroup.objects.filter(site=site).annotate(rack_count=Count('racks'))
    topology_maps = TopologyMap.objects.filter(site=site)

    return render(request, 'dcim/site.html', {
        'site': site,
        'stats': stats,
        'rack_groups': rack_groups,
        'topology_maps': topology_maps,
    })


class SiteEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_site'
    model = Site
    form_class = forms.SiteForm
    template_name = 'dcim/site_edit.html'
    cancel_url = 'dcim:site_list'


class SiteDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'dcim.delete_site'
    model = Site
    redirect_url = 'dcim:site_list'


class SiteBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.add_site'
    form = forms.SiteImportForm
    table = tables.SiteTable
    template_name = 'dcim/site_import.html'
    obj_list_url = 'dcim:site_list'


#
# Rack groups
#

class RackGroupListView(ObjectListView):
    queryset = RackGroup.objects.annotate(rack_count=Count('racks'))
    filter = filters.RackGroupFilter
    filter_form = forms.RackGroupFilterForm
    table = tables.RackGroupTable
    edit_permissions = ['dcim.change_rackgroup', 'dcim.delete_rackgroup']
    template_name = 'dcim/rackgroup_list.html'


class RackGroupEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_rackgroup'
    model = RackGroup
    form_class = forms.RackGroupForm
    cancel_url = 'dcim:rackgroup_list'


class RackGroupBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_rackgroup'
    cls = RackGroup
    form = forms.RackGroupBulkDeleteForm
    default_redirect_url = 'dcim:rackgroup_list'


#
# Racks
#

class RackListView(ObjectListView):
    queryset = Rack.objects.select_related('site').annotate(device_count=Count('devices', distinct=True))
    filter = filters.RackFilter
    filter_form = forms.RackFilterForm
    table = tables.RackTable
    edit_permissions = ['dcim.change_rack', 'dcim.delete_rack']
    template_name = 'dcim/rack_list.html'


def rack(request, pk):

    rack = get_object_or_404(Rack, pk=pk)

    nonracked_devices = Device.objects.filter(rack=rack, position__isnull=True)
    next_rack = Rack.objects.filter(site=rack.site, name__gt=rack.name).order_by('name').first()
    prev_rack = Rack.objects.filter(site=rack.site, name__lt=rack.name).order_by('-name').first()

    return render(request, 'dcim/rack.html', {
        'rack': rack,
        'nonracked_devices': nonracked_devices,
        'next_rack': next_rack,
        'prev_rack': prev_rack,
        'front_elevation': rack.get_front_elevation(),
        'rear_elevation': rack.get_rear_elevation(),
    })


class RackEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_rack'
    model = Rack
    form_class = forms.RackForm
    template_name = 'dcim/rack_edit.html'
    cancel_url = 'dcim:rack_list'


class RackDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'dcim.delete_rack'
    model = Rack
    redirect_url = 'dcim:rack_list'


class RackBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.add_rack'
    form = forms.RackImportForm
    table = tables.RackTable
    template_name = 'dcim/rack_import.html'
    obj_list_url = 'dcim:rack_list'


class RackBulkEditView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'dcim.change_rack'
    cls = Rack
    form = forms.RackBulkEditForm
    template_name = 'dcim/rack_bulk_edit.html'
    default_redirect_url = 'dcim:rack_list'

    def update_objects(self, pk_list, form):

        fields_to_update = {}
        for field in ['site', 'group', 'u_height', 'comments']:
            if form.cleaned_data[field]:
                fields_to_update[field] = form.cleaned_data[field]

        return self.cls.objects.filter(pk__in=pk_list).update(**fields_to_update)


class RackBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_rack'
    cls = Rack
    form = forms.RackBulkDeleteForm
    default_redirect_url = 'dcim:rack_list'


#
# Manufacturers
#

class ManufacturerListView(ObjectListView):
    queryset = Manufacturer.objects.annotate(devicetype_count=Count('device_types'))
    table = tables.ManufacturerTable
    edit_permissions = ['dcim.change_manufacturer', 'dcim.delete_manufacturer']
    template_name = 'dcim/manufacturer_list.html'


class ManufacturerEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_manufacturer'
    model = Manufacturer
    form_class = forms.ManufacturerForm
    success_url = 'dcim:manufacturer_list'
    cancel_url = 'dcim:manufacturer_list'


class ManufacturerBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_manufacturer'
    cls = Manufacturer
    form = forms.ManufacturerBulkDeleteForm
    default_redirect_url = 'dcim:manufacturer_list'


#
# Device types
#

class DeviceTypeListView(ObjectListView):
    queryset = DeviceType.objects.select_related('manufacturer')
    filter = filters.DeviceTypeFilter
    filter_form = forms.DeviceTypeFilterForm
    table = tables.DeviceTypeTable
    edit_permissions = ['dcim.change_devicetype', 'dcim.delete_devicetype']
    template_name = 'dcim/devicetype_list.html'


def devicetype(request, pk):

    devicetype = get_object_or_404(DeviceType, pk=pk)

    # Component tables
    consoleport_table = tables.ConsolePortTemplateTable(ConsolePortTemplate.objects.filter(device_type=devicetype))
    consoleserverport_table = tables.ConsoleServerPortTemplateTable(ConsoleServerPortTemplate.objects
                                                                    .filter(device_type=devicetype))
    powerport_table = tables.PowerPortTemplateTable(PowerPortTemplate.objects.filter(device_type=devicetype))
    poweroutlet_table = tables.PowerOutletTemplateTable(PowerOutletTemplate.objects.filter(device_type=devicetype))
    interface_table = tables.InterfaceTemplateTable(InterfaceTemplate.objects.filter(device_type=devicetype))
    if request.user.has_perm('dcim.change_devicetype'):
        consoleport_table.base_columns['pk'].visible = True
        consoleserverport_table.base_columns['pk'].visible = True
        powerport_table.base_columns['pk'].visible = True
        poweroutlet_table.base_columns['pk'].visible = True
        interface_table.base_columns['pk'].visible = True

    return render(request, 'dcim/devicetype.html', {
        'devicetype': devicetype,
        'consoleport_table': consoleport_table,
        'consoleserverport_table': consoleserverport_table,
        'powerport_table': powerport_table,
        'poweroutlet_table': poweroutlet_table,
        'interface_table': interface_table,
    })


class DeviceTypeEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_devicetype'
    model = DeviceType
    form_class = forms.DeviceTypeForm
    cancel_url = 'dcim:devicetype_list'


class DeviceTypeDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'dcim.delete_devicetype'
    model = DeviceType
    redirect_url = 'dcim:devicetype_list'


class DeviceTypeBulkEditView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'dcim.change_devicetype'
    cls = DeviceType
    form = forms.DeviceTypeBulkEditForm
    template_name = 'dcim/devicetype_bulk_edit.html'
    default_redirect_url = 'dcim:devicetype_list'

    def update_objects(self, pk_list, form):

        fields_to_update = {}
        for field in ['manufacturer', 'u_height']:
            if form.cleaned_data[field]:
                fields_to_update[field] = form.cleaned_data[field]

        return self.cls.objects.filter(pk__in=pk_list).update(**fields_to_update)


class DeviceTypeBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_devicetype'
    cls = DeviceType
    form = forms.DeviceTypeBulkDeleteForm
    default_redirect_url = 'dcim:devicetype_list'


#
# Device type components
#

class ComponentTemplateCreateView(View):
    model = None
    form = None

    def get(self, request, pk):

        devicetype = get_object_or_404(DeviceType, pk=pk)

        return render(request, 'dcim/component_template_add.html', {
            'devicetype': devicetype,
            'component_type': self.model._meta.verbose_name,
            'form': self.form(),
            'cancel_url': reverse('dcim:devicetype', kwargs={'pk': devicetype.pk}),
        })

    def post(self, request, pk):

        devicetype = get_object_or_404(DeviceType, pk=pk)

        form = self.form(request.POST)
        if form.is_valid():

            component_templates = []
            for name in form.cleaned_data['name_pattern']:
                component_template = self.form(request.POST).save(commit=False)
                component_template.device_type = devicetype
                component_template.name = name
                try:
                    component_template.full_clean()
                    component_templates.append(component_template)
                except ValidationError:
                    form.add_error('name_pattern', "Duplicate name found: {}".format(name))

            if not form.errors:
                self.model.objects.bulk_create(component_templates)
                messages.success(request, "Added {} component(s) to {}".format(len(component_templates), devicetype))
                if '_addanother' in request.POST:
                    return redirect(request.path)
                else:
                    return redirect('dcim:devicetype', pk=devicetype.pk)

        return render(request, 'dcim/component_template_add.html', {
            'devicetype': devicetype,
            'component_type': self.model._meta.verbose_name,
            'form': form,
            'cancel_url': reverse('dcim:devicetype', kwargs={'pk': devicetype.pk}),
        })


class ConsolePortTemplateAddView(ComponentTemplateCreateView):
    model = ConsolePortTemplate
    form = forms.ConsolePortTemplateForm


class ConsoleServerPortTemplateAddView(ComponentTemplateCreateView):
    model = ConsoleServerPortTemplate
    form = forms.ConsoleServerPortTemplateForm


class PowerPortTemplateAddView(ComponentTemplateCreateView):
    model = PowerPortTemplate
    form = forms.PowerPortTemplateForm


class PowerOutletTemplateAddView(ComponentTemplateCreateView):
    model = PowerOutletTemplate
    form = forms.PowerOutletTemplateForm


class InterfaceTemplateAddView(ComponentTemplateCreateView):
    model = InterfaceTemplate
    form = forms.InterfaceTemplateForm


def component_template_delete(request, pk, model):

    devicetype = get_object_or_404(DeviceType, pk=pk)

    class ComponentTemplateBulkDeleteForm(ConfirmationForm):
        pk = ModelMultipleChoiceField(queryset=model.objects.all(), widget=MultipleHiddenInput)

    if '_confirm' in request.POST:
        form = ComponentTemplateBulkDeleteForm(request.POST)
        if form.is_valid():

            # Delete component templates
            objects_to_delete = model.objects.filter(pk__in=[v.id for v in form.cleaned_data['pk']])
            try:
                deleted_count = objects_to_delete.count()
                objects_to_delete.delete()
            except ProtectedError, e:
                handle_protectederror(list(objects_to_delete), request, e)
                return redirect('dcim:devicetype', {'pk': devicetype.pk})

            messages.success(request, "Deleted {} {}".format(deleted_count, model._meta.verbose_name_plural))
            return redirect('dcim:devicetype', pk=devicetype.pk)

    else:
        form = ComponentTemplateBulkDeleteForm(initial={'pk': request.POST.getlist('pk')})

    selected_objects = model.objects.filter(pk__in=form.initial.get('pk'))
    if not selected_objects:
        messages.warning(request, "No {} were selected for deletion.".format(model._meta.verbose_name_plural))
        return redirect('dcim:devicetype', pk=devicetype.pk)

    return render(request, 'dcim/component_template_delete.html', {
        'devicetype': devicetype,
        'form': form,
        'selected_objects': selected_objects,
        'cancel_url': reverse('dcim:devicetype', kwargs={'pk': devicetype.pk}),
    })


#
# Device roles
#

class DeviceRoleListView(ObjectListView):
    queryset = DeviceRole.objects.annotate(device_count=Count('devices'))
    table = tables.DeviceRoleTable
    edit_permissions = ['dcim.change_devicerole', 'dcim.delete_devicerole']
    template_name = 'dcim/devicerole_list.html'


class DeviceRoleEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_devicerole'
    model = DeviceRole
    form_class = forms.DeviceRoleForm
    success_url = 'dcim:devicerole_list'
    cancel_url = 'dcim:devicerole_list'


class DeviceRoleBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_devicerole'
    cls = DeviceRole
    form = forms.DeviceRoleBulkDeleteForm
    default_redirect_url = 'dcim:devicerole_list'


#
# Platforms
#

class PlatformListView(ObjectListView):
    queryset = Platform.objects.annotate(device_count=Count('devices'))
    table = tables.PlatformTable
    edit_permissions = ['dcim.change_platform', 'dcim.delete_platform']
    template_name = 'dcim/platform_list.html'


class PlatformEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_platform'
    model = Platform
    form_class = forms.PlatformForm
    success_url = 'dcim:platform_list'
    cancel_url = 'dcim:platform_list'


class PlatformBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_platform'
    cls = Platform
    form = forms.PlatformBulkDeleteForm
    default_redirect_url = 'dcim:platform_list'


#
# Devices
#

class DeviceListView(ObjectListView):
    queryset = Device.objects.select_related('device_type__manufacturer', 'device_role', 'rack__site', 'primary_ip')
    filter = filters.DeviceFilter
    filter_form = forms.DeviceFilterForm
    table = tables.DeviceTable
    edit_permissions = ['dcim.change_device', 'dcim.delete_device']
    template_name = 'dcim/device_list.html'


def device(request, pk):

    device = get_object_or_404(Device, pk=pk)
    console_ports = ConsolePort.objects.filter(device=device).select_related('cs_port__device')
    cs_ports = ConsoleServerPort.objects.filter(device=device).select_related('connected_console')
    power_ports = PowerPort.objects.filter(device=device).select_related('power_outlet__device')
    power_outlets = PowerOutlet.objects.filter(device=device).select_related('connected_port')
    interfaces = Interface.objects.filter(device=device, mgmt_only=False)\
        .select_related('connected_as_a', 'connected_as_b', 'circuit')
    mgmt_interfaces = Interface.objects.filter(device=device, mgmt_only=True)\
        .select_related('connected_as_a', 'connected_as_b', 'circuit')

    # Gather any secrets which belong to this device
    secrets = device.secrets.all()

    # Find all IP addresses assigned to this device
    ip_addresses = IPAddress.objects.filter(interface__device=device).select_related('interface').order_by('address')

    # Find any related devices for convenient linking in the UI
    related_devices = []
    if device.name:
        if re.match('.+[0-9]+$', device.name):
            # Strip 1 or more trailing digits (e.g. core-switch1)
            base_name = re.match('(.*?)[0-9]+$', device.name).group(1)
        elif re.match('.+\d[a-z]$', device.name.lower()):
            # Strip a trailing letter if preceded by a digit (e.g. dist-switch3a -> dist-switch3)
            base_name = re.match('(.*\d+)[a-z]$', device.name.lower()).group(1)
        else:
            base_name = None
        if base_name:
            related_devices = Device.objects.filter(name__istartswith=base_name).exclude(pk=device.pk)\
                .select_related('rack', 'device_type__manufacturer')[:10]

    return render(request, 'dcim/device.html', {
        'device': device,
        'console_ports': console_ports,
        'cs_ports': cs_ports,
        'power_ports': power_ports,
        'power_outlets': power_outlets,
        'interfaces': interfaces,
        'mgmt_interfaces': mgmt_interfaces,
        'ip_addresses': ip_addresses,
        'secrets': secrets,
        'related_devices': related_devices,
    })


class DeviceEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'dcim.change_device'
    model = Device
    form_class = forms.DeviceForm
    fields_initial = ['site', 'rack', 'position', 'face']
    template_name = 'dcim/device_edit.html'
    cancel_url = 'dcim:device_list'


class DeviceDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'dcim.delete_device'
    model = Device
    redirect_url = 'dcim:device_list'


class DeviceBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.add_device'
    form = forms.DeviceImportForm
    table = tables.DeviceImportTable
    template_name = 'dcim/device_import.html'
    obj_list_url = 'dcim:device_list'


class DeviceBulkEditView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'dcim.change_device'
    cls = Device
    form = forms.DeviceBulkEditForm
    template_name = 'dcim/device_bulk_edit.html'
    default_redirect_url = 'dcim:device_list'

    def update_objects(self, pk_list, form):

        fields_to_update = {}
        if form.cleaned_data['platform']:
            fields_to_update['platform'] = form.cleaned_data['platform']
        elif form.cleaned_data['platform_delete']:
            fields_to_update['platform'] = None
        if form.cleaned_data['status']:
            status = form.cleaned_data['status']
            fields_to_update['status'] = True if status == 'True' else False
        for field in ['device_type', 'device_role', 'serial']:
            if form.cleaned_data[field]:
                fields_to_update[field] = form.cleaned_data[field]

        return self.cls.objects.filter(pk__in=pk_list).update(**fields_to_update)


class DeviceBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'dcim.delete_device'
    cls = Device
    form = forms.DeviceBulkDeleteForm
    default_redirect_url = 'dcim:device_list'


def device_inventory(request, pk):

    device = get_object_or_404(Device, pk=pk)
    modules = Module.objects.filter(device=device, parent=None).prefetch_related('submodules')

    return render(request, 'dcim/device_inventory.html', {
        'device': device,
        'modules': modules,
    })


def device_lldp_neighbors(request, pk):

    device = get_object_or_404(Device, pk=pk)
    interfaces = Interface.objects.filter(device=device).select_related('connected_as_a', 'connected_as_b')

    return render(request, 'dcim/device_lldp_neighbors.html', {
        'device': device,
        'interfaces': interfaces,
    })


#
# Console ports
#

@permission_required('dcim.add_consoleport')
def consoleport_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.ConsolePortCreateForm(request.POST)
        if form.is_valid():

            console_ports = []
            for name in form.cleaned_data['name_pattern']:
                cp_form = forms.ConsolePortForm({
                    'device': device.pk,
                    'name': name,
                })
                if cp_form.is_valid():
                    console_ports.append(cp_form.save(commit=False))
                else:
                    form.add_error('name_pattern', "Duplicate console port name for this device: {}".format(name))

            if not form.errors:
                ConsolePort.objects.bulk_create(console_ports)
                messages.success(request, "Added {} console port(s) to {}".format(len(console_ports), device))
                if '_addanother' in request.POST:
                    return redirect('dcim:consoleport_add', pk=device.pk)
                else:
                    return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.ConsolePortCreateForm()

    return render(request, 'dcim/consoleport_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_consoleport')
def consoleport_connect(request, pk):

    consoleport = get_object_or_404(ConsolePort, pk=pk)

    if request.method == 'POST':
        form = forms.ConsolePortConnectionForm(request.POST, instance=consoleport)
        if form.is_valid():
            consoleport = form.save()
            messages.success(request, "Connected {0} {1} to {2} {3}".format(
                consoleport.device,
                consoleport.name,
                consoleport.cs_port.device,
                consoleport.cs_port.name,
            ))
            return redirect('dcim:device', pk=consoleport.device.pk)

    else:
        form = forms.ConsolePortConnectionForm(instance=consoleport, initial={
            'rack': consoleport.device.rack,
            'connection_status': CONNECTION_STATUS_CONNECTED,
        })

    return render(request, 'dcim/consoleport_connect.html', {
        'consoleport': consoleport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleport.device.pk}),
    })


@permission_required('dcim.change_consoleport')
def consoleport_disconnect(request, pk):

    consoleport = get_object_or_404(ConsolePort, pk=pk)

    if not consoleport.cs_port:
        messages.warning(request, "Cannot disconnect console port {0}: It is not connected to anything"
                         .format(consoleport))
        return redirect('dcim:device', pk=consoleport.device.pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            consoleport.cs_port = None
            consoleport.connection_status = None
            consoleport.save()
            messages.success(request, "Console port {0} has been disconnected".format(consoleport))
            return redirect('dcim:device', pk=consoleport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/consoleport_disconnect.html', {
        'consoleport': consoleport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleport.device.pk}),
    })


@permission_required('dcim.change_consoleport')
def consoleport_edit(request, pk):

    consoleport = get_object_or_404(ConsolePort, pk=pk)

    if request.method == 'POST':
        form = forms.ConsolePortForm(request.POST, instance=consoleport)
        if form.is_valid():
            consoleport = form.save()
            messages.success(request, "Modified {0} {1}".format(consoleport.device.name, consoleport.name))
            return redirect('dcim:device', pk=consoleport.device.pk)

    else:
        form = forms.ConsolePortForm(instance=consoleport)

    return render(request, 'dcim/consoleport_edit.html', {
        'consoleport': consoleport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleport.device.pk}),
    })


@permission_required('dcim.delete_consoleport')
def consoleport_delete(request, pk):

    consoleport = get_object_or_404(ConsolePort, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            consoleport.delete()
            messages.success(request, "Console port {0} has been deleted from {1}".format(consoleport,
                                                                                          consoleport.device))
            return redirect('dcim:device', pk=consoleport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/consoleport_delete.html', {
        'consoleport': consoleport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleport.device.pk}),
    })


class ConsoleConnectionsBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.change_consoleport'
    form = forms.ConsoleConnectionImportForm
    table = tables.ConsoleConnectionTable
    template_name = 'dcim/console_connections_import.html'


#
# Console server ports
#

@permission_required('dcim.add_consoleserverport')
def consoleserverport_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.ConsoleServerPortCreateForm(request.POST)
        if form.is_valid():

            cs_ports = []
            for name in form.cleaned_data['name_pattern']:
                csp_form = forms.ConsoleServerPortForm({
                    'device': device.pk,
                    'name': name,
                })
                if csp_form.is_valid():
                    cs_ports.append(csp_form.save(commit=False))
                else:
                    form.add_error('name_pattern', "Duplicate console server port name for this device: {}"
                                   .format(name))

            if not form.errors:
                ConsoleServerPort.objects.bulk_create(cs_ports)
                messages.success(request, "Added {} console server port(s) to {}".format(len(cs_ports), device))
                if '_addanother' in request.POST:
                    return redirect('dcim:consoleserverport_add', pk=device.pk)
                else:
                    return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.ConsoleServerPortCreateForm()

    return render(request, 'dcim/consoleserverport_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_consoleserverport')
def consoleserverport_connect(request, pk):

    consoleserverport = get_object_or_404(ConsoleServerPort, pk=pk)

    if request.method == 'POST':
        form = forms.ConsoleServerPortConnectionForm(consoleserverport, request.POST)
        if form.is_valid():
            consoleport = form.cleaned_data['port']
            consoleport.cs_port = consoleserverport
            consoleport.connection_status = form.cleaned_data['connection_status']
            consoleport.save()
            messages.success(request, "Connected {0} {1} to {2} {3}".format(
                consoleport.device,
                consoleport.name,
                consoleserverport.device,
                consoleserverport.name,
            ))
            return redirect('dcim:device', pk=consoleserverport.device.pk)

    else:
        form = forms.ConsoleServerPortConnectionForm(consoleserverport, initial={'rack': consoleserverport.device.rack})

    return render(request, 'dcim/consoleserverport_connect.html', {
        'consoleserverport': consoleserverport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleserverport.device.pk}),
    })


@permission_required('dcim.change_consoleserverport')
def consoleserverport_disconnect(request, pk):

    consoleserverport = get_object_or_404(ConsoleServerPort, pk=pk)

    if not hasattr(consoleserverport, 'connected_console'):
        messages.warning(request, "Cannot disconnect console server port {0}: Nothing is connected to it"
                         .format(consoleserverport))
        return redirect('dcim:device', pk=consoleserverport.device.pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            consoleport = consoleserverport.connected_console
            consoleport.cs_port = None
            consoleport.connection_status = None
            consoleport.save()
            messages.success(request, "Console server port {0} has been disconnected".format(consoleserverport))
            return redirect('dcim:device', pk=consoleserverport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/consoleserverport_disconnect.html', {
        'consoleserverport': consoleserverport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleserverport.device.pk}),
    })


@permission_required('dcim.change_consoleserverport')
def consoleserverport_edit(request, pk):

    consoleserverport = get_object_or_404(ConsoleServerPort, pk=pk)

    if request.method == 'POST':
        form = forms.ConsoleServerPortForm(request.POST, instance=consoleserverport)
        if form.is_valid():
            consoleserverport = form.save()
            messages.success(request, "Modified {0} {1}".format(consoleserverport.device.name, consoleserverport.name))
            return redirect('dcim:device', pk=consoleserverport.device.pk)

    else:
        form = forms.ConsoleServerPortForm(instance=consoleserverport)

    return render(request, 'dcim/consoleserverport_edit.html', {
        'consoleserverport': consoleserverport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleserverport.device.pk}),
    })


@permission_required('dcim.delete_consoleserverport')
def consoleserverport_delete(request, pk):

    consoleserverport = get_object_or_404(ConsoleServerPort, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            consoleserverport.delete()
            messages.success(request, "Console server port {0} has been deleted from {1}"
                             .format(consoleserverport, consoleserverport.device))
            return redirect('dcim:device', pk=consoleserverport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/consoleserverport_delete.html', {
        'consoleserverport': consoleserverport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': consoleserverport.device.pk}),
    })


#
# Power ports
#

@permission_required('dcim.add_powerport')
def powerport_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.PowerPortCreateForm(request.POST)
        if form.is_valid():

            power_ports = []
            for name in form.cleaned_data['name_pattern']:
                pp_form = forms.PowerPortForm({
                    'device': device.pk,
                    'name': name,
                })
                if pp_form.is_valid():
                    power_ports.append(pp_form.save(commit=False))
                else:
                    form.add_error('name_pattern', "Duplicate power port name for this device: {}".format(name))

            if not form.errors:
                PowerPort.objects.bulk_create(power_ports)
                messages.success(request, "Added {} power port(s) to {}".format(len(power_ports), device))
                if '_addanother' in request.POST:
                    return redirect('dcim:powerport_add', pk=device.pk)
                else:
                    return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.PowerPortCreateForm()

    return render(request, 'dcim/powerport_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_powerport')
def powerport_connect(request, pk):

    powerport = get_object_or_404(PowerPort, pk=pk)

    if request.method == 'POST':
        form = forms.PowerPortConnectionForm(request.POST, instance=powerport)
        if form.is_valid():
            powerport = form.save()
            messages.success(request, "Connected {0} {1} to {2} {3}".format(
                powerport.device,
                powerport.name,
                powerport.power_outlet.device,
                powerport.power_outlet.name,
            ))
            return redirect('dcim:device', pk=powerport.device.pk)

    else:
        form = forms.PowerPortConnectionForm(instance=powerport, initial={
            'rack': powerport.device.rack,
            'connection_status': CONNECTION_STATUS_CONNECTED,
        })

    return render(request, 'dcim/powerport_connect.html', {
        'powerport': powerport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': powerport.device.pk}),
    })


@permission_required('dcim.change_powerport')
def powerport_disconnect(request, pk):

    powerport = get_object_or_404(PowerPort, pk=pk)

    if not powerport.power_outlet:
        messages.warning(request, "Cannot disconnect power port {0}: It is not connected to an outlet"
                         .format(powerport))
        return redirect('dcim:device', pk=powerport.device.pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            powerport.power_outlet = None
            powerport.connection_status = None
            powerport.save()
            messages.success(request, "Power port {0} has been disconnected".format(powerport))
            return redirect('dcim:device', pk=powerport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/powerport_disconnect.html', {
        'powerport': powerport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': powerport.device.pk}),
    })


@permission_required('dcim.change_powerport')
def powerport_edit(request, pk):

    powerport = get_object_or_404(PowerPort, pk=pk)

    if request.method == 'POST':
        form = forms.PowerPortForm(request.POST, instance=powerport)
        if form.is_valid():
            powerport = form.save()
            messages.success(request, "Modified {0} power port {1}".format(powerport.device.name, powerport.name))
            return redirect('dcim:device', pk=powerport.device.pk)

    else:
        form = forms.PowerPortForm(instance=powerport)

    return render(request, 'dcim/powerport_edit.html', {
        'powerport': powerport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': powerport.device.pk}),
    })


@permission_required('dcim.delete_powerport')
def powerport_delete(request, pk):

    powerport = get_object_or_404(PowerPort, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            powerport.delete()
            messages.success(request, "Power port {0} has been deleted from {1}".format(powerport, powerport.device))
            return redirect('dcim:device', pk=powerport.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/powerport_delete.html', {
        'powerport': powerport,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': powerport.device.pk}),
    })


class PowerConnectionsBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.change_powerport'
    form = forms.PowerConnectionImportForm
    table = tables.PowerConnectionTable
    template_name = 'dcim/power_connections_import.html'


#
# Power outlets
#

@permission_required('dcim.add_poweroutlet')
def poweroutlet_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.PowerOutletCreateForm(request.POST)
        if form.is_valid():

            power_outlets = []
            for name in form.cleaned_data['name_pattern']:
                po_form = forms.PowerOutletForm({
                    'device': device.pk,
                    'name': name,
                })
                if po_form.is_valid():
                    power_outlets.append(po_form.save(commit=False))
                else:
                    form.add_error('name_pattern', "Duplicate power outlet name for this device: {}".format(name))

            if not form.errors:
                PowerOutlet.objects.bulk_create(power_outlets)
                messages.success(request, "Added {} power outlet(s) to {}".format(len(power_outlets), device))
                if '_addanother' in request.POST:
                    return redirect('dcim:poweroutlet_add', pk=device.pk)
                else:
                    return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.PowerOutletCreateForm()

    return render(request, 'dcim/poweroutlet_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_poweroutlet')
def poweroutlet_connect(request, pk):

    poweroutlet = get_object_or_404(PowerOutlet, pk=pk)

    if request.method == 'POST':
        form = forms.PowerOutletConnectionForm(poweroutlet, request.POST)
        if form.is_valid():
            powerport = form.cleaned_data['port']
            powerport.power_outlet = poweroutlet
            powerport.connection_status = form.cleaned_data['connection_status']
            powerport.save()
            messages.success(request, "Connected {0} {1} to {2} {3}".format(
                powerport.device,
                powerport.name,
                poweroutlet.device,
                poweroutlet.name,
            ))
            return redirect('dcim:device', pk=poweroutlet.device.pk)

    else:
        form = forms.PowerOutletConnectionForm(poweroutlet, initial={'rack': poweroutlet.device.rack})

    return render(request, 'dcim/poweroutlet_connect.html', {
        'poweroutlet': poweroutlet,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': poweroutlet.device.pk}),
    })


@permission_required('dcim.change_poweroutlet')
def poweroutlet_disconnect(request, pk):

    poweroutlet = get_object_or_404(PowerOutlet, pk=pk)

    if not hasattr(poweroutlet, 'connected_port'):
        messages.warning(request, "Cannot disconnect power outlet {0}: Nothing is connected to it".format(poweroutlet))
        return redirect('dcim:device', pk=poweroutlet.device.pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            powerport = poweroutlet.connected_port
            powerport.power_outlet = None
            powerport.connection_status = None
            powerport.save()
            messages.success(request, "Power outlet {0} has been disconnected".format(poweroutlet))
            return redirect('dcim:device', pk=poweroutlet.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/poweroutlet_disconnect.html', {
        'poweroutlet': poweroutlet,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': poweroutlet.device.pk}),
    })


@permission_required('dcim.change_poweroutlet')
def poweroutlet_edit(request, pk):

    poweroutlet = get_object_or_404(PowerOutlet, pk=pk)

    if request.method == 'POST':
        form = forms.PowerOutletForm(request.POST, instance=poweroutlet)
        if form.is_valid():
            poweroutlet = form.save()
            messages.success(request, "Modified {0} power outlet {1}".format(poweroutlet.device.name, poweroutlet.name))
            return redirect('dcim:device', pk=poweroutlet.device.pk)

    else:
        form = forms.PowerOutletForm(instance=poweroutlet)

    return render(request, 'dcim/poweroutlet_edit.html', {
        'poweroutlet': poweroutlet,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': poweroutlet.device.pk}),
    })


@permission_required('dcim.delete_poweroutlet')
def poweroutlet_delete(request, pk):

    poweroutlet = get_object_or_404(PowerOutlet, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            poweroutlet.delete()
            messages.success(request, "Power outlet {0} has been deleted from {1}".format(poweroutlet,
                                                                                          poweroutlet.device))
            return redirect('dcim:device', pk=poweroutlet.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/poweroutlet_delete.html', {
        'poweroutlet': poweroutlet,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': poweroutlet.device.pk}),
    })


#
# Interfaces
#

@permission_required('dcim.add_interface')
def interface_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.InterfaceCreateForm(request.POST)
        if form.is_valid():

            interfaces = []
            for name in form.cleaned_data['name_pattern']:
                iface_form = forms.InterfaceForm({
                    'device': device.pk,
                    'name': name,
                    'form_factor': form.cleaned_data['form_factor'],
                    'mgmt_only': form.cleaned_data['mgmt_only'],
                    'description': form.cleaned_data['description'],
                })
                if iface_form.is_valid():
                    interfaces.append(iface_form.save(commit=False))
                else:
                    form.add_error('name_pattern', "Duplicate interface name for this device: {}".format(name))

            if not form.errors:
                Interface.objects.bulk_create(interfaces)
                messages.success(request, "Added {} interface(s) to {}".format(len(interfaces), device))
                if '_addanother' in request.POST:
                    return redirect('dcim:interface_add', pk=device.pk)
                else:
                    return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.InterfaceCreateForm()

    return render(request, 'dcim/interface_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_interface')
def interface_edit(request, pk):

    interface = get_object_or_404(Interface, pk=pk)

    if request.method == 'POST':
        form = forms.InterfaceForm(request.POST, instance=interface)
        if form.is_valid():
            interface = form.save()
            messages.success(request, "Modified {0} interface {1}".format(interface.device.name, interface.name))
            return redirect('dcim:device', pk=interface.device.pk)

    else:
        form = forms.InterfaceForm(instance=interface)

    return render(request, 'dcim/interface_edit.html', {
        'interface': interface,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': interface.device.pk}),
    })


@permission_required('dcim.delete_interface')
def interface_delete(request, pk):

    interface = get_object_or_404(Interface, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            interface.delete()
            messages.success(request, "Interface {0} has been deleted from {1}".format(interface, interface.device))
            return redirect('dcim:device', pk=interface.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/interface_delete.html', {
        'interface': interface,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': interface.device.pk}),
    })


class InterfaceBulkAddView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'dcim.add_interface'
    cls = Device
    form = forms.InterfaceBulkCreateForm
    template_name = 'dcim/interface_bulk_add.html'
    default_redirect_url = 'dcim:device_list'

    def update_objects(self, pk_list, form):

        selected_devices = Device.objects.filter(pk__in=pk_list)
        interfaces = []

        for device in selected_devices:
            for name in form.cleaned_data['name_pattern']:
                iface_form = forms.InterfaceForm({
                    'device': device.pk,
                    'name': name,
                    'form_factor': form.cleaned_data['form_factor'],
                    'mgmt_only': form.cleaned_data['mgmt_only'],
                    'description': form.cleaned_data['description'],
                })
                if iface_form.is_valid():
                    interfaces.append(iface_form.save(commit=False))
                else:
                    form.add_error(None, "Duplicate interface {} found for device {}".format(name, device))

        if not form.errors:
            Interface.objects.bulk_create(interfaces)
            messages.success(self.request, "Added {} interfaces to {} devices".format(len(interfaces),
                                                                                      len(selected_devices)))


#
# Interface connections
#

@permission_required('dcim.add_interfaceconnection')
def interfaceconnection_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.InterfaceConnectionForm(device, request.POST)
        if form.is_valid():
            interfaceconnection = form.save()
            messages.success(request, "Connected {0} {1} to {2} {3}".format(
                interfaceconnection.interface_a.device,
                interfaceconnection.interface_a,
                interfaceconnection.interface_b.device,
                interfaceconnection.interface_b,
            ))
            if '_addanother' in request.POST:
                base_url = reverse('dcim:interfaceconnection_add', kwargs={'pk': device.pk})
                params = urlencode({
                    'rack_b': interfaceconnection.interface_b.device.rack.pk,
                    'device_b': interfaceconnection.interface_b.device.pk,
                })
                return HttpResponseRedirect('{}?{}'.format(base_url, params))
            else:
                return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.InterfaceConnectionForm(device, initial={
            'interface_a': request.GET.get('interface', None),
            'rack_b': request.GET.get('rack_b', None),
            'device_b': request.GET.get('device_b', None),
        })

    return render(request, 'dcim/interfaceconnection_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.delete_interfaceconnection')
def interfaceconnection_delete(request, pk):

    interfaceconnection = get_object_or_404(InterfaceConnection, pk=pk)
    device_id = request.GET.get('device', None)

    if request.method == 'POST':
        form = forms.InterfaceConnectionDeletionForm(request.POST)
        if form.is_valid():
            interfaceconnection.delete()
            messages.success(request, "Deleted the connection between {0} {1} and {2} {3}".format(
                interfaceconnection.interface_a.device,
                interfaceconnection.interface_a,
                interfaceconnection.interface_b.device,
                interfaceconnection.interface_b,
            ))
            if form.cleaned_data['device']:
                return redirect('dcim:device', pk=form.cleaned_data['device'].pk)
            else:
                return redirect('dcim:device_list')

    else:
        form = forms.InterfaceConnectionDeletionForm(initial={
            'device': device_id,
        })

    # Determine where to direct user upon cancellation
    if device_id:
        cancel_url = reverse('dcim:device', kwargs={'pk': device_id})
    else:
        cancel_url = reverse('dcim:device_list')

    return render(request, 'dcim/interfaceconnection_delete.html', {
        'interfaceconnection': interfaceconnection,
        'device_id': device_id,
        'form': form,
        'cancel_url': cancel_url,
    })


class InterfaceConnectionsBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'dcim.change_interface'
    form = forms.InterfaceConnectionImportForm
    table = tables.InterfaceConnectionTable
    template_name = 'dcim/interface_connections_import.html'


#
# Connections
#

class ConsoleConnectionsListView(ObjectListView):
    queryset = ConsolePort.objects.select_related('device', 'cs_port__device').filter(cs_port__isnull=False)\
        .order_by('cs_port__device__name', 'cs_port__name')
    filter = filters.ConsoleConnectionFilter
    filter_form = forms.ConsoleConnectionFilterForm
    table = tables.ConsoleConnectionTable
    template_name = 'dcim/console_connections_list.html'


class PowerConnectionsListView(ObjectListView):
    queryset = PowerPort.objects.select_related('device', 'power_outlet__device').filter(power_outlet__isnull=False)\
        .order_by('power_outlet__device__name', 'power_outlet__name')
    filter = filters.PowerConnectionFilter
    filter_form = forms.PowerConnectionFilterForm
    table = tables.PowerConnectionTable
    template_name = 'dcim/power_connections_list.html'


class InterfaceConnectionsListView(ObjectListView):
    queryset = InterfaceConnection.objects.select_related('interface_a__device', 'interface_b__device')\
        .order_by('interface_a__device__name', 'interface_a__name')
    filter = filters.InterfaceConnectionFilter
    filter_form = forms.InterfaceConnectionFilterForm
    table = tables.InterfaceConnectionTable
    template_name = 'dcim/interface_connections_list.html'


#
# IP addresses
#

@permission_required('ipam.add_ipaddress')
def ipaddress_assign(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.IPAddressForm(device, request.POST)
        if form.is_valid():

            ipaddress = form.save(commit=False)
            ipaddress.interface = form.cleaned_data['interface']
            ipaddress.save()
            messages.success(request, "Added new IP address {0} to interface {1}".format(ipaddress,
                                                                                         ipaddress.interface))

            if form.cleaned_data['set_as_primary']:
                device.primary_ip = ipaddress
                device.save()

            if '_addanother' in request.POST:
                return redirect('dcim:ipaddress_assign', pk=device.pk)
            else:
                return redirect('dcim:device', pk=device.pk)

    else:
        form = forms.IPAddressForm(device)

    return render(request, 'dcim/ipaddress_assign.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device', kwargs={'pk': device.pk}),
    })


#
# Modules
#

@permission_required('dcim.add_module')
def module_add(request, pk):

    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        form = forms.ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.device = device
            module.save()
            messages.success(request, "Added module {} to {}".format(module.name, module.device.name))
            if '_addanother' in request.POST:
                return redirect('dcim:module_add', pk=module.device.pk)
            else:
                return redirect('dcim:device_inventory', pk=module.device.pk)

    else:
        form = forms.ModuleForm()

    return render(request, 'dcim/module_edit.html', {
        'device': device,
        'form': form,
        'cancel_url': reverse('dcim:device_inventory', kwargs={'pk': device.pk}),
    })


@permission_required('dcim.change_module')
def module_edit(request, pk):

    module = get_object_or_404(Module, pk=pk)

    if request.method == 'POST':
        form = forms.ModuleForm(request.POST, instance=module)
        if form.is_valid():
            module = form.save()
            messages.success(request, "Modified {} module {}".format(module.device.name, module.name))
            return redirect('dcim:device_inventory', pk=module.device.pk)

    else:
        form = forms.ModuleForm(instance=module)

    return render(request, 'dcim/module_edit.html', {
        'module': module,
        'form': form,
        'cancel_url': reverse('dcim:device_inventory', kwargs={'pk': module.device.pk}),
    })


@permission_required('dcim.delete_module')
def module_delete(request, pk):

    module = get_object_or_404(Module, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            module.delete()
            messages.success(request, "Module {} has been deleted from {}".format(module, module.device))
            return redirect('dcim:device_inventory', pk=module.device.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'dcim/module_delete.html', {
        'module': module,
        'form': form,
        'cancel_url': reverse('dcim:device_inventory', kwargs={'pk': module.device.pk}),
    })
