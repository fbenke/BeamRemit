from django.contrib import admin

from pricing.models import Pricing, ExchangeRate, Comparison, Limit, Fee,\
    end_previous_object

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
            return ('id', 'start', 'end', 'markup', 'fee', 'site')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'markup', 'fee', 'site')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Pricing, site=obj.site)
            obj.save()

    list_filter = ('site',)

admin.site.register(Pricing, PricingAdmin)


class FeeAdmin(admin.ModelAdmin):

    form = forms.FeeForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'fee', 'currency', 'site')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'end', 'fee', 'currency', 'site')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Fee, site=obj.site, currency=obj.currency)
            obj.save()

    list_filter = ('site', 'currency')

admin.site.register(Fee, FeeAdmin)


class ExchangeRateAdmin(DoNotDeleteModelAdmin):

    form = forms.ExchangeRateForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'gbp_ghs', 'gbp_usd', 'gbp_sll', 'gbp_eur')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'gbp_ghs', 'gbp_usd', 'gbp_sll', 'gbp_eur')

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
            'transaction_min_receiving', 'transaction_max_receiving',
            'sending_currency', 'receiving_currency')

        if obj:
            return ('id', 'start', 'end', 'site', 'user_limit_basic',
                    'user_limit_complete', 'transaction_min',
                    'transaction_max') + calculated_fields
        else:
            return ('id', 'start', 'end') + calculated_fields

    list_display = ('id', 'end', 'site', 'user_limit_basic',
                    'user_limit_complete', 'transaction_min',
                    'transaction_max')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Limit, site=obj.site)
            obj.save()

    list_filter = ('site',)

admin.site.register(Limit, LimitAdmin)
