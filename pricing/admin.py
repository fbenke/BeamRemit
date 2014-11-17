from django.contrib import admin

from pricing.models import Pricing, ExchangeRate, Comparison, Limit,\
    end_previous_object, end_previous_object_by_site

from pricing import forms


class DoNotDeleteModelAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(DoNotDeleteModelAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


class PricingAdmin(DoNotDeleteModelAdmin):

    form = forms.PricingForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'markup', 'fee', 'fee_currency', 'site')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'markup', 'fee', 'fee_currency', 'site')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object_by_site(Pricing, obj.site)
            obj.save()

admin.site.register(Pricing, PricingAdmin)


class ExchangeRateAdmin(DoNotDeleteModelAdmin):

    form = forms.ExchangeRateForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'gbp_ghs', 'gbp_usd', 'gbp_sll')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'gbp_ghs', 'gbp_usd', 'gbp_sll')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(ExchangeRate)
            obj.save()

admin.site.register(ExchangeRate, ExchangeRateAdmin)


class ComparisonAdmin(DoNotDeleteModelAdmin):

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


class LimitAdmin(DoNotDeleteModelAdmin):

    form = forms.LimitForm

    def get_readonly_fields(self, request, obj=None):

        calculated_fields = (
            'transaction_min_ghs', 'transaction_max_ghs',
            'transaction_min_sll', 'transaction_max_sll'
        )

        if obj:
            return ('id', 'start', 'end', 'site', 'user_limit_basic',
                    'user_limit_complete', 'transaction_min',
                    'transaction_max', 'currency') + calculated_fields
        else:
            return ('id', 'start', 'end') + calculated_fields

    list_display = ('id', 'start', 'end', 'site', 'user_limit_basic',
                    'user_limit_complete', 'transaction_min',
                    'transaction_max', 'currency')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object_by_site(Limit, obj.site)
            obj.save()

admin.site.register(Limit, LimitAdmin)
