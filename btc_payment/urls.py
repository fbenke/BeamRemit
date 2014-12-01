from django.conf.urls import patterns, url
from django.contrib import admin

from btc_payment import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^gocoin/$',
        views.ConfirmGoCoinPayment.as_view(),
        name='gocoin'
    ),
    url(
        r'^blockchain/$',
        views.ConfirmBlockchainPayment.as_view(),
        name='blockchain'
    ),
)
