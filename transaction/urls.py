from django.conf.urls import patterns, url
from django.contrib import admin

from transaction import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^pricing/$',
        views.PricingViewSet.as_view({'post': 'create'}),
        name='pricing'
    ),
    url(
        r'^pricing/(?P<pk>[0-9]+)/$',
        views.PricingViewSet.as_view({'get': 'retrieve'}),
        name='pricing-detail'
    ),
    url(
        r'^pricing/current/$',
        views.PricingCurrent.as_view(),
        name='pricing-current'
    ),
    url(
        r'^add/$',
        views.CreateTransaction.as_view(),
        name='transaction-add'
    ),
    url(
        r'^list/$',
        views.ViewTransactions.as_view(),
        name='transaction-list'
    )
)
