from django.conf import settings
from django.contrib import admin

from btc_payment.models import GoCoinInvoice, BlockchainInvoice, BlockchainPayment


class InvoiceAdmin(admin.ModelAdmin):

    def transaction_url(self, obj):
        path = settings.API_BASE_URL + '/admin/transaction/transaction'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.transaction.id, obj.transaction.id)
    transaction_url.allow_tags = True
    transaction_url.short_description = 'transaction'


class GoCoinInvoiceAdmin(InvoiceAdmin):

    readonly_fields = (
        'transaction_url', 'invoice_id', 'btc_address', 'btc_usd',
        'sender_usd', 'state', 'balance_due'
    )
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'invoice_id', 'transaction_url', 'state')

    list_filter = ('state', )

admin.site.register(GoCoinInvoice, GoCoinInvoiceAdmin)


class BlockchainPaymentChangeInline(admin.TabularInline):

    model = BlockchainPayment
    readonly_fields = ('state', 'received_at', 'amount', 'input_transaction_hash', 'forward_transaction_hash')
    extra = 0
    max_num = 0
    can_delete = False


class BlockchainInvoiceAdmin(InvoiceAdmin):

    readonly_fields = (
        'transaction_url', 'invoice_id', 'created_at', 'btc_address', 'btc_usd',
        'sender_usd', 'state', 'balance_due'
    )
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'invoice_id', 'transaction_url', 'state')

    inlines = (BlockchainPaymentChangeInline, )

admin.site.register(BlockchainInvoice, BlockchainInvoiceAdmin)
