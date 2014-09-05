from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin
from django.contrib import admin

from userena.admin import UserenaAdmin
from userena.utils import get_user_model


class CustomUserenaAdmin(UserenaAdmin):
    list_display = ('id', 'email', 'is_staff', 'is_active', 'date_joined')
    list_display_links = ('id', 'email')


class CustomTokenAdmin(TokenAdmin):
    list_display = ('key', 'created', 'user')

try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), CustomUserenaAdmin)

admin.site.unregister(Token)
admin.site.register(Token, CustomTokenAdmin)
