from django.conf import settings
from django.contrib.sites.models import Site

from beam.utils.log import log_error


def get_frontend_domain(request):
    try:
        return request.META.get('HTTP_REFERER').split('?')[0].split('#!')[0].split(settings.PROTOCOL + '://')[1].replace('/', '')
    except (IndexError, AttributeError):
        return request.META.get('HTTP_REFERER')


def get_site_by_request(request):

    if not settings.MULTIPLE_SITE_SUPPORT:
        return Site.objects.get_current()

    try:
        frontend_domain = get_frontend_domain(request)
        return Site.objects.get(domain__iexact=frontend_domain)
    except (Site.DoesNotExist, ValueError):
        message = 'ERROR - Site Mapping: Cannot associate {} with a Site. {} {}'.format(frontend_domain, request.META, request.DATA)
        log_error(message)
        return Site.objects.get_current()


def get_country_blacklist_by_request(request):

    try:
        bae_project_site = settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_USER_SL]

        if get_frontend_domain(request) == bae_project_site:
            return list(set(settings.COUNTRY_BLACKLIST) - set(('US',)))

    except KeyError:
        pass

    return settings.COUNTRY_BLACKLIST
