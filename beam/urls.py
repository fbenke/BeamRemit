from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView

from beam.settings import STATIC_URL

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(
        r'^$',
        TemplateView.as_view(template_name='index.html'),
        name='home'
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
        RedirectView.as_view(url=STATIC_URL + 'img/favicon.ico')
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





