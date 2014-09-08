from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from django.contrib import admin

from userena.admin import UserenaAdmin
from userena.utils import get_user_model

from accounts.models import BeamProfile


class BeamProfileAdmin(admin.ModelAdmin):

    def user_email(self, obj):
        return obj.user.email

    def user_id(self, obj):
        return obj.user.id

    def user_name(self, obj):
        return '{} {}'.format(obj.user.first_name, obj.user.last_name)

    readonly_fields = ('user_id', 'user_email', 'user_name')

    read_and_write_fields = (
        'date_of_birth', 'street',
        'post_code', 'city', 'country'
    )

    fields = readonly_fields + read_and_write_fields

    list_display = ('user_email', 'country', 'city')

    list_display_links = ('user_email',)


class CustomUserenaAdmin(UserenaAdmin):

    list_display = ('id', 'email', 'is_staff', 'is_active', 'date_joined')
    list_display_links = ('id', 'email')


class CustomTokenAdmin(TokenAdmin):

    def user_email(self, obj):
        return obj.user.email

    def user_id(self, obj):
        return obj.user.id

    list_display = ('user_email', 'key', 'created')

    readonly_fields = ('user_id', 'user_email', 'key')
    fields = readonly_fields

try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), CustomUserenaAdmin)

try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass
admin.site.register(Token, CustomTokenAdmin)

admin.site.register(BeamProfile, BeamProfileAdmin)
