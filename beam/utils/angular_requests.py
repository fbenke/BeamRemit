from django.conf import settings
from django.contrib.sites.models import Site

from beam.utils.log import log_error


def get_frontend_domain(request):
    try:
        return request.META.get('HTTP_REFERER').split('?')[0].split(settings.PROTOCOL + '://')[1].replace('/', '')
    except (IndexError, AttributeError):
        return request.META.get('HTTP_REFERER')


def get_site_by_request(request):
    try:
        frontend_domain = get_frontend_domain(request)
        return Site.objects.get(domain__iexact=frontend_domain)
    except (Site.DoesNotExist, ValueError):
        post_data = request.DATA
        message = 'ERROR - Site Mapping: Cannot associate {} with a Site. {} {}'.format(frontend_domain, request.META, post_data)
        log_error(message)
        return Site.objects.get_current()


def get_country_blacklist_by_request(request):

    bae_project_site = settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_USER_SL]

    if get_frontend_domain(request) == bae_project_site:

        return list(set(settings.COUNTRY_BLACKLIST) - set(('US',)))

    else:
        return settings.COUNTRY_BLACKLIST
