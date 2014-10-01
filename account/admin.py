from django.conf import settings
from django.contrib import admin

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from userena.admin import UserenaAdmin
from userena.utils import get_user_model

from account.models import BeamProfile


class BeamProfileAdmin(admin.ModelAdmin):

    def user_url(self, obj):
        path = settings.API_BASE_URL + '/admin/auth/user'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.user.id, obj.user.id)
    user_url.allow_tags = True
    user_url.short_description = 'user'

    def user_email(self, obj):
        return obj.user.email

    def user_id(self, obj):
        return obj.user.id

    def user_name(self, obj):
        return '{} {}'.format(obj.user.first_name, obj.user.last_name)

    readonly_fields = (
        'user_url', 'user_email', 'user_name', 'date_of_birth',
        'street', 'post_code', 'city', 'country'
    )

    read_and_write_fields = ()
        
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
