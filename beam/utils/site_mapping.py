from django.conf import settings
from django.contrib.sites.models import Site

from beam.utils.logging import log_error


def get_site_by_request(request):

    if settings.ENV == settings.ENV_LOCAL:
        return Site.objects.get_current()
    try:
        host = request.META.get('HTTP_REFERER').replace(settings.PROTOCOL, '').replace('/', '').replace(':', '')
        print host
        return Site.objects.get(domain__iexact=host)
    except Site.DoesNotExist:
        message = 'ERROR - Site Mapping: Cannot associate {} with a Site'.format(host)
        log_error(message)
        return Site.objects.get_current()
