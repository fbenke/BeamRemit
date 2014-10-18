from django.contrib.gis.geoip import GeoIP
from django.conf import settings

from rest_framework import permissions


class IsNotOnCountryBlacklist(permissions.BasePermission):

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def has_permission(self, request, view):
        ip_address = self._get_client_ip(request)
        print ip_address
        g = GeoIP()
        print g.country(ip_address)
        return not g.country(ip_address)['country_code'] in settings.COUNTRY_BLACKLIST
