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
            return ('id', 'start', 'end', 'markup', 'fee', 'gbp_ghs')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee')

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
        if obj:
            return ('id', 'start', 'end', 'min_gbp', 'max_gbp', 'min_ghs',
                    'max_ghs', 'daily_limit_gbp_basic', 'daily_limit_ghs_basic',
                    'daily_limit_gbp_complete', 'daily_limit_ghs_complete')
        else:
            return ('id', 'start', 'end', 'min_ghs', 'max_ghs',
                    'daily_limit_ghs_basic', 'daily_limit_ghs_complete')

    list_display = ('id', 'start', 'end', 'max_gbp',
                    'daily_limit_gbp_basic', 'daily_limit_gbp_complete')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Limit)
            obj.save()

admin.site.register(Limit, LimitAdmin)
