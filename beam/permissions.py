from django.contrib.gis.geoip import GeoIP
from django.conf import settings

from rest_framework import permissions


class IsNotOnCountryBlacklist(permissions.BasePermission):

    def has_permission(self, request, view):
        ip_address = request.META['REMOTE_ADDR']
        print ip_address
        g = GeoIP()
        print g.country(ip_address)
        return not g.country(ip_address)['country_code'] in settings.COUNTRY_BLACKLIST
