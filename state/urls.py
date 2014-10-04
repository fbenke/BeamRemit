from django.conf.urls import patterns, url
from django.contrib import admin

from state import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.GetState.as_view(),
        name='current'
    )
)
