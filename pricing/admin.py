from django.contrib import admin

from pricing.models import Pricing, Comparison, end_previous_object

from pricing import forms


class PricingAdmin(admin.ModelAdmin):

    form = forms.PricingForm

    readonly_fields = ('id', 'start', 'end')
    read_and_write_fields = ('markup', 'gbp_ghs', 'fee')
    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'start', 'end', 'markup', 'gbp_ghs', 'fee')

    # remove linsk to forbid editing (change to built in solution in Django 1.7)
    def __init__(self, *args, **kwargs):
        super(PricingAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    # this would remove the list-view altogether
    # def has_change_permission(self, request, obj=None):
    #     return False

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Pricing)
        obj.save()

admin.site.register(Pricing, PricingAdmin)


class ComparisonAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'start', 'end')
    read_and_write_fields = ('price_comparison', )
    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'start', 'end')

    # remove linsk to forbid editing (change to built in solution in Django 1.7)
    def __init__(self, *args, **kwargs):
        super(ComparisonAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def save_model(self, request, obj, form, change):
        if not obj.id:
            end_previous_object(Comparison)
        obj.save()

admin.site.register(Comparison, ComparisonAdmin)
