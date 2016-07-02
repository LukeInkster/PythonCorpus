from django.conf.urls import url

from .views import *


urlpatterns = [

    # VRFs
    url(r'^vrfs/$', VRFListView.as_view(), name='vrf_list'),
    url(r'^vrfs/(?P<pk>\d+)/$', VRFDetailView.as_view(), name='vrf_detail'),

    # Roles
    url(r'^roles/$', RoleListView.as_view(), name='role_list'),
    url(r'^roles/(?P<pk>\d+)/$', RoleDetailView.as_view(), name='role_detail'),

    # RIRs
    url(r'^rirs/$', RIRListView.as_view(), name='rir_list'),
    url(r'^rirs/(?P<pk>\d+)/$', RIRDetailView.as_view(), name='rir_detail'),

    # Aggregates
    url(r'^aggregates/$', AggregateListView.as_view(), name='aggregate_list'),
    url(r'^aggregates/(?P<pk>\d+)/$', AggregateDetailView.as_view(), name='aggregate_detail'),

    # Prefixes
    url(r'^prefixes/$', PrefixListView.as_view(), name='prefix_list'),
    url(r'^prefixes/(?P<pk>\d+)/$', PrefixDetailView.as_view(), name='prefix_detail'),

    # IP addresses
    url(r'^ip-addresses/$', IPAddressListView.as_view(), name='ipaddress_list'),
    url(r'^ip-addresses/(?P<pk>\d+)/$', IPAddressDetailView.as_view(), name='ipaddress_detail'),

    # VLANs
    url(r'^vlans/$', VLANListView.as_view(), name='vlan_list'),
    url(r'^vlans/(?P<pk>\d+)/$', VLANDetailView.as_view(), name='vlan_detail'),

]
