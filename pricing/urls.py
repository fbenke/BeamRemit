from django.conf.urls import patterns, url
from django.contrib import admin

from pricing import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.PricingViewSet.as_view({'post': 'create'}),
        name='add'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        views.PricingViewSet.as_view({'get': 'retrieve'}),
        name='detail'
    ),
    url(
        r'^current/$',
        views.PricingCurrent.as_view(),
        name='current'
    ),
)
