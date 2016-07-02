from django.conf.urls import url

from . import views


urlpatterns = [

    # Secret roles
    url(r'^secret-roles/$', views.SecretRoleListView.as_view(), name='secretrole_list'),
    url(r'^secret-roles/add/$', views.SecretRoleEditView.as_view(), name='secretrole_add'),
    url(r'^secret-roles/delete/$', views.SecretRoleBulkDeleteView.as_view(), name='secretrole_bulk_delete'),
    url(r'^secret-roles/(?P<slug>[\w-]+)/edit/$', views.SecretRoleEditView.as_view(), name='secretrole_edit'),

    # Secrets
    url(r'^secrets/$', views.SecretListView.as_view(), name='secret_list'),
    url(r'^secrets/import/$', views.secret_import, name='secret_import'),
    url(r'^secrets/edit/$', views.SecretBulkEditView.as_view(), name='secret_bulk_edit'),
    url(r'^secrets/delete/$', views.SecretBulkDeleteView.as_view(), name='secret_bulk_delete'),
    url(r'^secrets/(?P<pk>\d+)/$', views.secret, name='secret'),
    url(r'^secrets/(?P<pk>\d+)/edit/$', views.secret_edit, name='secret_edit'),
    url(r'^secrets/(?P<pk>\d+)/delete/$', views.SecretDeleteView.as_view(), name='secret_delete'),

]
