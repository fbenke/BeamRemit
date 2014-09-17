from django.contrib import admin

from btc_payment.models import GoCoinInvoice


class GoCoinInvoiceAdmin(admin.ModelAdmin):

    readonly_fields = ('transaction', 'invoice_id', 'btc_address')
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'invoice_id')

admin.site.register(GoCoinInvoice, GoCoinInvoiceAdmin)
