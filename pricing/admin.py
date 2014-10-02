from django.contrib import admin

from pricing.models import Pricing, Comparison, end_previous_object

from pricing import forms


class PricingAdmin(admin.ModelAdmin):

    form = forms.PricingForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'markup', 'fee', 'gbp_ghs')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Pricing)
            obj.save()

admin.site.register(Pricing, PricingAdmin)


class ComparisonAdmin(admin.ModelAdmin):

    # readonly_fields = ('id', 'start', 'end')
    # read_and_write_fields = ('price_comparison', )
    # fields = readonly_fields + read_and_write_fields

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'price_comparison')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Comparison)
            obj.save()

admin.site.register(Comparison, ComparisonAdmin)
