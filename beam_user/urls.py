from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from beam_user import views


user_list = views.BeamUserViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = patterns(
    '',
    url(
        r'^create/$',
        views.CreateUserView.as_view(),
        name='create'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        user_list,
        name='change'
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
