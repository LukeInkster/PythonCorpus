from rest_framework import generics
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

from dcim.models import (
    ConsolePort, ConsoleServerPort, Device, DeviceRole, DeviceType, IFACE_FF_VIRTUAL, Interface, InterfaceConnection,
    Manufacturer, Platform, PowerOutlet, PowerPort, Rack, RackGroup, Site,
)
from dcim import filters
from .exceptions import MissingFilterException
from . import serializers
from extras.api.renderers import BINDZoneRenderer, FlatJSONRenderer
from utilities.api import ServiceUnavailable


#
# Sites
#

class SiteListView(generics.ListAPIView):
    """
    List all sites
    """
    queryset = Site.objects.all()
    serializer_class = serializers.SiteSerializer


class SiteDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single site
    """
    queryset = Site.objects.all()
    serializer_class = serializers.SiteSerializer


#
# Rack groups
#

class RackGroupListView(generics.ListAPIView):
    """
    List all rack groups
    """
    queryset = RackGroup.objects.all()
    serializer_class = serializers.RackGroupSerializer
    filter_class = filters.RackGroupFilter


class RackGroupDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single rack group
    """
    queryset = RackGroup.objects.all()
    serializer_class = serializers.RackGroupSerializer


#
# Racks
#

class RackListView(generics.ListAPIView):
    """
    List racks (filterable)
    """
    queryset = Rack.objects.select_related('site')
    serializer_class = serializers.RackSerializer
    filter_class = filters.RackFilter


class RackDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single rack
    """
    queryset = Rack.objects.select_related('site')
    serializer_class = serializers.RackDetailSerializer


#
# Rack units
#

class RackUnitListView(APIView):
    """
    List rack units (by rack)
    """

    def get(self, request, pk):

        rack = get_object_or_404(Rack, pk=pk)
        face = request.GET.get('face', 0)
        elevation = rack.get_rack_units(face)

        # Serialize Devices within the rack elevation
        for u in elevation:
            if u['device']:
                u['device'] = serializers.DeviceNestedSerializer(instance=u['device']).data

        return Response(elevation)


#
# Manufacturers
#

class ManufacturerListView(generics.ListAPIView):
    """
    List all hardware manufacturers
    """
    queryset = Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer


class ManufacturerDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single hardware manufacturers
    """
    queryset = Manufacturer.objects.all()
    serializer_class = serializers.ManufacturerSerializer


#
# Device Types
#

class DeviceTypeListView(generics.ListAPIView):
    """
    List device types (filterable)
    """
    queryset = DeviceType.objects.select_related('manufacturer')
    serializer_class = serializers.DeviceTypeSerializer
    filter_class = filters.DeviceTypeFilter


class DeviceTypeDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single device type
    """
    queryset = DeviceType.objects.select_related('manufacturer')
    serializer_class = serializers.DeviceTypeDetailSerializer


#
# Device roles
#

class DeviceRoleListView(generics.ListAPIView):
    """
    List all device roles
    """
    queryset = DeviceRole.objects.all()
    serializer_class = serializers.DeviceRoleSerializer


class DeviceRoleDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single device role
    """
    queryset = DeviceRole.objects.all()
    serializer_class = serializers.DeviceRoleSerializer


#
# Platforms
#

class PlatformListView(generics.ListAPIView):
    """
    List all platforms
    """
    queryset = Platform.objects.all()
    serializer_class = serializers.PlatformSerializer


class PlatformDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single platform
    """
    queryset = Platform.objects.all()
    serializer_class = serializers.PlatformSerializer


#
# Devices
#

class DeviceListView(generics.ListAPIView):
    """
    List devices (filterable)
    """
    queryset = Device.objects.select_related('device_type__manufacturer', 'device_role', 'platform', 'rack__site')\
        .prefetch_related('primary_ip__nat_outside')
    serializer_class = serializers.DeviceSerializer
    filter_class = filters.DeviceFilter
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [BINDZoneRenderer, FlatJSONRenderer]


class DeviceDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single device
    """
    queryset = Device.objects.all()
    serializer_class = serializers.DeviceSerializer


#
# Console ports
#

class ConsolePortListView(generics.ListAPIView):
    """
    List console ports (by device)
    """
    serializer_class = serializers.ConsolePortSerializer

    def get_queryset(self):

        device = get_object_or_404(Device, pk=self.kwargs['pk'])
        return ConsolePort.objects.filter(device=device).select_related('cs_port')


class ConsolePortView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = serializers.ConsolePortSerializer
    queryset = ConsolePort.objects.all()


#
# Console server ports
#

class ConsoleServerPortListView(generics.ListAPIView):
    """
    List console server ports (by device)
    """
    serializer_class = serializers.ConsoleServerPortSerializer

    def get_queryset(self):

        device = get_object_or_404(Device, pk=self.kwargs['pk'])
        return ConsoleServerPort.objects.filter(device=device).select_related('connected_console')


#
# Power ports
#

class PowerPortListView(generics.ListAPIView):
    """
    List power ports (by device)
    """
    serializer_class = serializers.PowerPortSerializer

    def get_queryset(self):

        device = get_object_or_404(Device, pk=self.kwargs['pk'])
        return PowerPort.objects.filter(device=device).select_related('power_outlet')


class PowerPortView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = serializers.PowerPortSerializer
    queryset = PowerPort.objects.all()


#
# Power outlets
#

class PowerOutletListView(generics.ListAPIView):
    """
    List power outlets (by device)
    """
    serializer_class = serializers.PowerOutletSerializer

    def get_queryset(self):

        device = get_object_or_404(Device, pk=self.kwargs['pk'])
        return PowerOutlet.objects.filter(device=device).select_related('connected_port')


#
# Interfaces
#

class InterfaceListView(generics.ListAPIView):
    """
    List interfaces (by device)
    """
    serializer_class = serializers.InterfaceSerializer
    filter_class = filters.InterfaceFilter

    def get_queryset(self):

        device = get_object_or_404(Device, pk=self.kwargs['pk'])
        queryset = Interface.objects.filter(device=device).select_related('connected_as_a', 'connected_as_b')

        # Filter by type (physical or virtual)
        iface_type = self.request.query_params.get('type')
        if iface_type == 'physical':
            queryset = queryset.exclude(form_factor=IFACE_FF_VIRTUAL)
        elif iface_type == 'virtual':
            queryset = queryset.filter(form_factor=IFACE_FF_VIRTUAL)
        elif iface_type is not None:
            queryset = queryset.empty()

        return queryset


class InterfaceDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single interface
    """
    queryset = Interface.objects.select_related('device')
    serializer_class = serializers.InterfaceDetailSerializer


class InterfaceConnectionView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = serializers.InterfaceConnectionSerializer
    queryset = InterfaceConnection.objects.all()


#
# Live queries
#

class LLDPNeighborsView(APIView):
    """
    Retrieve live LLDP neighbors of a device
    """

    def get(self, request, pk):

        device = get_object_or_404(Device, pk=pk)
        if not device.primary_ip:
            raise ServiceUnavailable(detail="No IP configured for this device.")

        RPC = device.get_rpc_client()
        if not RPC:
            raise ServiceUnavailable(detail="No RPC client available for this platform ({}).".format(device.platform))

        # Connect to device and retrieve inventory info
        try:
            with RPC(device, username=settings.NETBOX_USERNAME, password=settings.NETBOX_PASSWORD) as rpc_client:
                lldp_neighbors = rpc_client.get_lldp_neighbors()
        except:
            raise ServiceUnavailable(detail="Error connecting to the remote device.")

        return Response(lldp_neighbors)


#
# Miscellaneous
#

class RelatedConnectionsView(APIView):
    """
    Retrieve all connections related to a given console/power/interface connection
    """

    def get(self, request):

        peer_device = request.GET.get('peer-device')
        peer_interface = request.GET.get('peer-interface')

        # Search by interface
        if peer_device and peer_interface:

            # Determine local interface from peer interface's connection
            try:
                peer_iface = Interface.objects.get(device__name=peer_device, name=peer_interface)
            except Interface.DoesNotExist:
                raise Http404()
            local_iface = peer_iface.get_connected_interface()
            if local_iface:
                device = local_iface.device
            else:
                return Response()

        else:
            raise MissingFilterException(detail='Must specify search parameters (peer-device and peer-interface).')

        # Initialize response skeleton
        response = dict()
        response['device'] = serializers.DeviceSerializer(device).data
        response['console-ports'] = []
        response['power-ports'] = []
        response['interfaces'] = []

        # Build console connections
        console_ports = ConsolePort.objects.filter(device=device).select_related('cs_port__device')
        for cp in console_ports:
            cp_info = dict()
            cp_info['name'] = cp.name
            if cp.cs_port:
                cp_info['console-server'] = cp.cs_port.device.name
                cp_info['port'] = cp.cs_port.name
            else:
                cp_info['console-server'] = None
                cp_info['port'] = None
            response['console-ports'].append(cp_info)

        # Build power connections
        power_ports = PowerPort.objects.filter(device=device).select_related('power_outlet__device')
        for pp in power_ports:
            pp_info = dict()
            pp_info['name'] = pp.name
            if pp.power_outlet:
                pp_info['pdu'] = pp.power_outlet.device.name
                pp_info['outlet'] = pp.power_outlet.name
            else:
                pp_info['pdu'] = None
                pp_info['outlet'] = None
            response['power-ports'].append(pp_info)

        # Built interface connections
        interfaces = Interface.objects.filter(device=device)
        for iface in interfaces:
            iface_info = dict()
            iface_info['name'] = iface.name
            peer_interface = iface.get_connected_interface()
            if peer_interface:
                iface_info['device'] = peer_interface.device.name
                iface_info['interface'] = peer_interface.name
            else:
                iface_info['device'] = None
                iface_info['interface'] = None
            response['interfaces'].append(iface_info)

        return Response(response)
