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
        r'^(?P<pk>[0-9]+)/$',
        views.RetrieveUserView.as_view(),
        name='retrieve'
    ),
)

urlpatterns = format_suffix_patterns(urlpatterns)
