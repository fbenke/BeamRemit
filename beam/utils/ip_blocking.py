from django.conf import settings
from django.contrib.gis.geoip import GeoIP


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def country_blocked(request):
    ip_address = get_client_ip(request)
    g = GeoIP()
    return g.country(ip_address)['country_code'] in settings.COUNTRY_BLACKLIST

HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS = 451
