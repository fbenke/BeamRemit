from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from beam_user import views


urlpatterns = patterns(
    '',
    url(
        r'^create/$',
        views.CreateUserView.as_view(),
        name='create'
    ),
    url(
        r'^edit/(?P<pk>[0-9]+)/$',
        views.EditUserView.as_view(),
        name='edit'
    ),
    url(
        r'^view/(?P<pk>[0-9]+)/$',
        views.RetrieveUserView.as_view(),
        name='retrieve'
    ),
    url(
        r'^login/$',
        views.Login.as_view(),
        name='login'
    ),
    url(
        r'^logout/$',
        'beam_user.views.logout',
        name='logout'
    ),
)

urlpatterns = format_suffix_patterns(urlpatterns)
