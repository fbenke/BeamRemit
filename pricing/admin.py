from django.contrib import admin

from pricing.models import Pricing, Comparison, Limit, end_previous_object

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


class LimitAdmin(admin.ModelAdmin):

    form = forms.LimitForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'min_gbp', 'max_gbp', 'min_ghs', 'max_ghs')
        else:
            return ('id', 'start', 'end', 'min_ghs', 'max_ghs')

    list_display = ('id', 'start', 'end', 'max_ghs', 'max_gbp')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Limit)
            obj.save()

admin.site.register(Limit, LimitAdmin)
