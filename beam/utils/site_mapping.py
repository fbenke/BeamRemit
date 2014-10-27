from django.conf import settings
from django.contrib.sites.models import Site


def get_site_by_request(request):
    host = request.META.get('HTTP_REFERER').replace(settings.PROTOCOL, '').replace('/', '')
    return Site.objects.get(domain__iexact=host)
