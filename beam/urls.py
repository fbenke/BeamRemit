from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView

from django.conf import settings

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        TemplateView.as_view(template_name='index.html'),
        name='home'
    ),
    url(
        r'^api/v1/account/',
        include('account.urls', namespace='account')
    ),
    url(
        r'^api/v1/pricing/',
        include('pricing.urls', namespace='pricing')
    ),
    url(
        r'^api/v1/transaction/',
        include('transaction.urls', namespace='transaction')
    ),
    url(
        r'^api/v1/btc_payment/',
        include('btc_payment.urls', namespace='btc_payment')
    ),
    url(
        r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots'
    ),
    url(
        r'^humans\.txt$',
        TemplateView.as_view(template_name='humans.txt', content_type='text/plain'),
        name='humans'
    ),
    url(
        r'^favicon\.ico$',
        RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.png')
    ),
    url(
        r'^admin/',
        include(admin.site.urls)),
    url(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
)

handler404 = 'beam.views.page_not_found'
handler500 = 'beam.views.custom_error'
handler403 = 'beam.views.permission_denied'
handler400 = 'beam.views.bad_request'
