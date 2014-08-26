from django.contrib import admin

from beam_user.models import BeamUser


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'password')
    read_and_write_fields = ('email', 'first_name', 'last_name', 'is_active', 'is_admin',)
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'email', 'is_admin', 'is_active',)
    list_display_links = ('email',)
    list_filter = ('is_active', 'is_admin', )
    search_fields = ('email', 'first_name', 'last_name',)

admin.site.register(BeamUser, UserAdmin)
