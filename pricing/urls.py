from django.conf.urls import patterns, url
from django.contrib import admin

from pricing import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.PricingCurrent.as_view(),
        name='current'
    ),
    # url(
    #     r'^comparison/$',
    #     views.PriceComparison.as_view(),
    #     name='comparison'
    # ),

)
