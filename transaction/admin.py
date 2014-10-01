from django.conf import settings
from django.contrib import admin

from transaction.models import Recipient, Transaction


class RecipientAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'first_name', 'last_name', 'phone_number', 'notification_email')
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'first_name', 'last_name', 'phone_number')

admin.site.register(Recipient, RecipientAdmin)


class TransactionAdmin(admin.ModelAdmin):

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

    def recipient_url(self, obj):
        path = settings.API_BASE_URL + '/admin/transaction/recipient'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.recipient.id, obj.recipient.id)
    recipient_url.allow_tags = True
    recipient_url.short_description = 'recipient'

    readonly_fields = (
        'id', 'recipient_url', 'pricing_url', 'sender_url', 'amount_gbp', 'amount_btc',
        'amount_ghs', 'reference_number', 'initialized_at', 'paid_at',
        'processed_at', 'cancelled_at', 'invalidated_at',
    )

    read_and_write_fields = ('state', 'comments')
    fields = read_and_write_fields + readonly_fields

    list_display = ('id', 'sender_url', 'reference_number', 'state')

admin.site.register(Transaction, TransactionAdmin)
