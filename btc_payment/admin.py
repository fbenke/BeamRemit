from django.conf import settings
from django.contrib import admin

from btc_payment.models import GoCoinInvoice


class GoCoinInvoiceAdmin(admin.ModelAdmin):

    def transaction_url(self, obj):
        path = settings.API_BASE_URL + '/admin/transaction/transaction'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.transaction.id, obj.transaction.id)
    transaction_url.allow_tags = True
    transaction_url.short_description = 'transaction'

    readonly_fields = (
        'transaction_url', 'invoice_id', 'btc_address', 'btc_usd',
        'sender_usd', 'state'
    )
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'invoice_id', 'transaction_url', 'state')

admin.site.register(GoCoinInvoice, GoCoinInvoiceAdmin)
