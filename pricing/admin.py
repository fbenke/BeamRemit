from django.contrib import admin

from pricing.models import Pricing


class PricingAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'start')

    read_and_write_fields = ('markup', 'gbp_ghs', 'fee', 'end')

    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee')

admin.site.register(Pricing, PricingAdmin)
