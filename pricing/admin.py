from django.contrib import admin

from pricing.models import Pricing, Comparison, Limit, end_previous_object

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
            return ('id', 'start', 'end', 'markup', 'fee_gbp', 'fee_usd', 'gbp_ghs', 'gbp_usd', 'gbp_sll')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee_gbp', 'fee_usd')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Pricing)
            obj.save()

admin.site.register(Pricing, PricingAdmin)


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
            'user_limit_basic_usd', 'user_limit_complete_usd',
            'transaction_min_usd', 'transaction_max_usd',
            'transaction_min_ghs', 'transaction_max_ghs',
            'transaction_min_sll', 'transaction_max_sll'
        )

        if obj:
            return ('id', 'start', 'end', 'user_limit_basic_gbp',
                    'user_limit_complete_gbp', 'transaction_min_gbp',
                    'transaction_max_gbp') + calculated_fields
        else:
            return ('id', 'start', 'end') + calculated_fields

    list_display = ('id', 'start', 'end', 'user_limit_basic_gbp',
                    'user_limit_complete_gbp', 'transaction_min_gbp',
                    'transaction_max_gbp')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Limit)
            obj.save()

admin.site.register(Limit, LimitAdmin)
