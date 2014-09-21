from django.contrib import admin

from transaction.models import Recipient, Transaction


class RecipientAdmin(admin.ModelAdmin):

    readonly_fields = ('id', 'first_name', 'last_name', 'phone_number', 'notification_email')
    read_and_write_fields = ()
    fields = readonly_fields + read_and_write_fields
    list_display = ('id', 'first_name', 'last_name', 'phone_number')

admin.site.register(Recipient, RecipientAdmin)


class TransactionAdmin(admin.ModelAdmin):

    def sender_email(self, obj):
        return obj.sender.email

    readonly_fields = (
        'id', 'recipient', 'pricing', 'sender_email', 'amount_gbp', 'amount_btc',
        'amount_ghs', 'reference_number', 'initialized_at', 'paid_at', 'processed_at',
        'cancelled_at', 'invalidated_at'
    )

    read_and_write_fields = ('state',)
    fields = read_and_write_fields + readonly_fields
    list_display = ('id', 'sender_email', 'reference_number', 'state')
    list_display_links = ('id', 'sender_email')


admin.site.register(Transaction, TransactionAdmin)
