from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from transaction.models import Recipient, Transaction


class RecipientAdmin(admin.ModelAdmin):

    def amount_to_be_paid(self, obj):
        return obj.transactions.get(recipient=obj.id).received_amount

    def country(self, obj):
        return obj.transactions.get(recipient=obj.id).receiving_country

    readonly_fields = (
        'id', 'first_name', 'last_name', 'phone_number',
        'amount_to_be_paid', 'country'
    )
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'first_name', 'last_name', 'phone_number')

admin.site.register(Recipient, RecipientAdmin)


class TransactionAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):

        if 'state' in form.changed_data:

            if obj.state == Transaction.PROCESSED:

                obj.post_processed()

                obj.processed_at = timezone.now()

            elif obj.state == Transaction.CANCELLED:
                obj.cancelled_at = timezone.now()

            elif obj.state == Transaction.PAID:
                obj.paid_at = timezone.now()

        obj.save()

    def sender_url(self, obj):
        path = settings.API_BASE_URL + '/admin/account/beamprofile'
        return '<a href="{}/{}/">{} {}</a>'.format(
            path, obj.sender.profile.id, obj.sender.first_name, obj.sender.last_name)

    sender_url.allow_tags = True
    sender_url.short_description = 'sender'

    def pricing_url(self, obj):
        path = settings.API_BASE_URL + '/admin/pricing/pricing'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.pricing.id, obj.pricing.id)

    pricing_url.allow_tags = True
    pricing_url.short_description = 'pricing'

    def fee_url(self, obj):
        path = settings.API_BASE_URL + '/admin/pricing/fee'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.fee.id, obj.fee.id)

    fee_url.allow_tags = True
    fee_url.short_description = 'fee'

    def exchange_rate_url(self, obj):
        path = settings.API_BASE_URL + '/admin/pricing/exchangerate'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.exchange_rate.id, obj.exchange_rate.id)

    exchange_rate_url.allow_tags = True
    exchange_rate_url.short_description = 'exchange_rate'

    def sender_email(self, obj):
        return obj.sender.email

    def recipient_url(self, obj):
        path = settings.API_BASE_URL + '/admin/transaction/recipient'
        return '<a href="{}/{}/">{} {}</a>'.format(
            path, obj.recipient.id, obj.recipient.first_name, obj.recipient.last_name)

    recipient_url.allow_tags = True
    recipient_url.short_description = 'recipient'

    def amount_paid_to_beam(self, obj):
        return obj.sent_amount + obj.fee.amount

    def payment_processor_invoice(self, obj):
        invoice_class = settings.PROCESSOR_INVOICE_CLASS[obj.payment_processor][0]
        invoice_referer = settings.PROCESSOR_INVOICE_CLASS[obj.payment_processor][1]
        path = settings.API_BASE_URL + '/admin/btc_payment/' + invoice_class.lower()
        invoice = getattr(obj, invoice_referer)
        return '<a href="{}/{}/">{}</a>'.format(path, invoice.id, invoice.id)

    payment_processor_invoice.allow_tags = True
    payment_processor_invoice.short_description = 'invoice'

    readonly_fields = (
        'id', 'recipient_url', 'pricing_url', 'exchange_rate_url', 'fee_url', 'sender_url', 'receiving_country',
        'sent_amount', 'sent_currency', 'received_amount', 'amount_paid_to_beam', 'payment_processor',
        'amount_btc', 'reference_number', 'initialized_at', 'paid_at', 'processed_at',
        'cancelled_at', 'invalidated_at', 'received_currency', 'payment_processor_invoice'
    )

    fieldsets = (
        (None, {
            'fields': (
                'id', 'pricing_url', 'fee_url', 'exchange_rate_url',
                ('payment_processor_invoice', 'payment_processor'),
                'amount_btc', 'reference_number')
        }),
        ('Sender', {
            'fields': (
                'sender_url', ('sent_amount', 'sent_currency', 'amount_paid_to_beam')
            )
        }),
        ('Recipient', {
            'fields': (
                'recipient_url', ('received_amount', 'received_currency', 'receiving_country')
            )
        }),
        ('Status', {
            'classes': ('collapse',),
            'fields': (
                'initialized_at', 'paid_at', 'processed_at', 'cancelled_at', 'invalidated_at',
                'state', 'comments'
            )
        }),
    )

    list_display = (
        'id', 'sender_email', 'reference_number', 'state', 'sent_amount',
        'sent_currency', 'received_amount', 'receiving_country'
    )

    list_filter = ('state', 'initialized_at', 'paid_at')

    search_fields = ('id', 'reference_number')

    list_per_page = 20

admin.site.register(Transaction, TransactionAdmin)
