from django.contrib import admin

from pricing.models import Pricing


class PricingAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'start', 'end', 'markup', 'ghs_usd')
    read_and_write_fields = ()

    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'start', 'end', 'markup', 'ghs_usd')

admin.site.register(Pricing, PricingAdmin)
