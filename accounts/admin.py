from django.contrib import admin
from userena.models import UserenaSignup


class UserenaSignupAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
        'last_active',
        'activation_key',
        'activation_notification_send',
        'email_unconfirmed',
        'email_confirmation_key',
        'email_confirmation_key_created',
    )
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    # list_display = ('id', 'email', 'is_admin', 'is_active',)
    # list_display_links = ('email',)
    # list_filter = ('is_active', 'is_admin', )
    # search_fields = ('email', 'first_name', 'last_name',)

admin.site.register(UserenaSignup, UserenaSignupAdmin)
