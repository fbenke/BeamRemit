from django.contrib import admin

from pricing.models import Pricing

from pricing import forms


class PricingAdmin(admin.ModelAdmin):

    form = forms.PricingForm

    readonly_fields = ('id', 'start', 'end')

    read_and_write_fields = ('markup', 'gbp_ghs', 'fee')

    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee')

    def save_model(self, request, obj, form, change):
        Pricing.end_previous_pricing()
        obj.save()

admin.site.register(Pricing, PricingAdmin)
