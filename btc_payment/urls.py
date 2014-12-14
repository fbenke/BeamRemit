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
    url(
        r'^blockchain/pricing/$',
        views.BlockchainPricing.as_view(),
        name='blockchain-pricing'
    ),
    url(
        r'^coinapult/$',
        views.ConfirmCoinapultPayment.as_view(),
        name='coinapult'
    ),
    url(
        r'^coinapult/pricing/$',
        views.CoinapultPricing.as_view(),
        name='coinapult-pricing'
    )

)
