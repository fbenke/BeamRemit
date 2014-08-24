from django.contrib import admin

from beam_user.models import BeamUser


class UserAdmin(admin.ModelAdmin):
    fields = ('email', 'first_name', 'last_name', 'is_active', 'is_admin', )
    readonly_fields = ('password',)
    list_display = ('email', 'is_admin',)
    list_display_links = ('email',)
    list_filter = ('is_active', 'is_admin', )
    search_fields = ('email', 'first_name', 'last_name',)

admin.site.register(BeamUser, UserAdmin)
