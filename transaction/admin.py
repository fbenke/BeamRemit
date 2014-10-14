from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from transaction.models import Recipient, Transaction


class RecipientAdmin(admin.ModelAdmin):

    def amount_ghs_to_be_paid(self, obj):
        return obj.transactions.get(recipient=obj.id).amount_ghs

    readonly_fields = ('id', 'first_name', 'last_name', 'phone_number', 'notification_email', 'amount_ghs_to_be_paid')
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'first_name', 'last_name', 'phone_number')

admin.site.register(Recipient, RecipientAdmin)


class TransactionAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if obj.state == Transaction.PROCESSED:
            obj.processed_at = timezone.now()
        elif obj.state == Transaction.CANCELLED:
            obj.cancelled_at = timezone.now()
        obj.save()

    def sender_url(self, obj):
        path = settings.API_BASE_URL + '/admin/account/beamprofile'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.sender.profile.id, obj.sender.email)
    sender_url.allow_tags = True
    sender_url.short_description = 'sender'

    def pricing_url(self, obj):
        path = settings.API_BASE_URL + '/admin/pricing/pricing'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.pricing.id, obj.pricing.id)
    pricing_url.allow_tags = True
    pricing_url.short_description = 'pricing'

    def sender_email(self, obj):
        return obj.sender.email

    def recipient_url(self, obj):
        path = settings.API_BASE_URL + '/admin/transaction/recipient'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.recipient.id, obj.recipient.id)
    recipient_url.allow_tags = True
    recipient_url.short_description = 'recipient'

    def british_pound_paid_to_beam(self, obj):
        return obj.amount_gbp + obj.pricing.fee

    readonly_fields = (
        'id', 'recipient_url', 'pricing_url', 'sender_url', 'amount_gbp', 'british_pound_paid_to_beam',
        'amount_btc', 'amount_ghs', 'reference_number', 'initialized_at', 'paid_at', 'processed_at',
        'cancelled_at', 'invalidated_at',
    )

    read_and_write_fields = ('state', 'comments')

    fields = readonly_fields + read_and_write_fields

    list_display = ('id', 'sender_email', 'reference_number', 'state', 'amount_gbp')

    list_filter = ('state', 'initialized_at', 'paid_at')

    search_fields = ('id', 'reference_number')

    list_per_page = 20

admin.site.register(Transaction, TransactionAdmin)
