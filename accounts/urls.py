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
    # Account activation
    url(
        r'^activate/(?P<activation_key>\w+)/$',
        views.Activation.as_view(),
        name='activate'
    ),
    # Retry activation
    url(r'^activate/retry/(?P<activation_key>\w+)/$',
        views.ActivationRetry.as_view(),
        name='activate_retry'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
