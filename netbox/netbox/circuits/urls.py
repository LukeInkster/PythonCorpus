from django.conf.urls import url

from . import views


urlpatterns = [

    # Providers
    url(r'^providers/$', views.ProviderListView.as_view(), name='provider_list'),
    url(r'^providers/add/$', views.ProviderEditView.as_view(), name='provider_add'),
    url(r'^providers/import/$', views.ProviderBulkImportView.as_view(), name='provider_import'),
    url(r'^providers/edit/$', views.ProviderBulkEditView.as_view(), name='provider_bulk_edit'),
    url(r'^providers/delete/$', views.ProviderBulkDeleteView.as_view(), name='provider_bulk_delete'),
    url(r'^providers/(?P<slug>[\w-]+)/$', views.provider, name='provider'),
    url(r'^providers/(?P<slug>[\w-]+)/edit/$', views.ProviderEditView.as_view(), name='provider_edit'),
    url(r'^providers/(?P<slug>[\w-]+)/delete/$', views.ProviderDeleteView.as_view(), name='provider_delete'),

    # Circuit types
    url(r'^circuit-types/$', views.CircuitTypeListView.as_view(), name='circuittype_list'),
    url(r'^circuit-types/add/$', views.CircuitTypeEditView.as_view(), name='circuittype_add'),
    url(r'^circuit-types/delete/$', views.CircuitTypeBulkDeleteView.as_view(), name='circuittype_bulk_delete'),
    url(r'^circuit-types/(?P<slug>[\w-]+)/edit/$', views.CircuitTypeEditView.as_view(), name='circuittype_edit'),

    # Circuits
    url(r'^circuits/$', views.CircuitListView.as_view(), name='circuit_list'),
    url(r'^circuits/add/$', views.CircuitEditView.as_view(), name='circuit_add'),
    url(r'^circuits/import/$', views.CircuitBulkImportView.as_view(), name='circuit_import'),
    url(r'^circuits/edit/$', views.CircuitBulkEditView.as_view(), name='circuit_bulk_edit'),
    url(r'^circuits/delete/$', views.CircuitBulkDeleteView.as_view(), name='circuit_bulk_delete'),
    url(r'^circuits/(?P<pk>\d+)/$', views.circuit, name='circuit'),
    url(r'^circuits/(?P<pk>\d+)/edit/$', views.CircuitEditView.as_view(), name='circuit_edit'),
    url(r'^circuits/(?P<pk>\d+)/delete/$', views.CircuitDeleteView.as_view(), name='circuit_delete'),

]
