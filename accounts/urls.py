from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from accounts import views

urlpatterns = patterns(
    '',
    url(
        r'^signup/$',
        views.Signup.as_view(),
        name='signup'
    ),
    url(
        r'^activate/(?P<activation_key>\w+)/$',
        views.Activation.as_view(),
        name='activate'
    ),
    url(
        r'^activate/retry/(?P<activation_key>\w+)/$',
        views.ActivationRetry.as_view(),
        name='activate_retry'
    ),
    url(
        r'^signin/$',
        views.Signin.as_view(),
        name='signin'
    ),
    url(
        r'^signout/$',
        views.Signout.as_view(),
        name='signout'
    ),
)

urlpatterns = format_suffix_patterns(urlpatterns)
