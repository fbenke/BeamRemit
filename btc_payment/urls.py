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
    # url(
    #     r'^confirm_payment/$',
    #     views.ConfirmPayment.as_view(),
    #     name='confirm_payment'
    # ),
)
