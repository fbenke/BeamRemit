from django.conf import settings
from django.contrib.sites.models import Site


def get_site_by_request(request):

    if settings.ENV == settings.ENV_LOCAL:
        return Site.objects.get_current()

    host = request.META.get('HTTP_REFERER').replace(settings.PROTOCOL, '').replace('/', '')
    print host
    return Site.objects.get(domain__iexact=host)
