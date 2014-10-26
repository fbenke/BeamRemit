from django.conf.urls import patterns, url
from django.contrib import admin

from transaction import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^add/$',
        views.CreateTransaction.as_view(),
        name='add'
    ),
    url(
        r'^$',
        views.ViewTransactions.as_view(),
        name='list'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        views.GetTransaction.as_view(),
        name='list'
    ),
    url(
        r'^test/$',
        views.Test.as_view()
    ),
)
