from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from accounts import views

urlpatterns = patterns(
    '',
    url(
        r'^signup/$',
        views.SignupView.as_view(),
        name='accounts_signup'
    ),
)

urlpatterns = format_suffix_patterns(urlpatterns)
