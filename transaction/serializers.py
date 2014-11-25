from django.conf import settings
from django.db import transaction as dbtransaction

from rest_framework import serializers
from rest_framework import fields

from transaction import models, constants

from pricing.models import get_current_pricing, get_current_exchange_rate


class TransactionSerializer(serializers.ModelSerializer):

    received_currency = fields.FloatField()

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = (
            'id', 'recipient', 'sent_amount', 'sent_currency', 'amount_btc', 'received_amount',
            'reference_number', 'state', 'initialized_at', 'paid_at', 'processed_at'
        )
        fields = read_only_fields + ('received_currency',)


class CreateTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = ()
        read_and_write_fields = ('recipient', 'sent_amount', 'receiving_country', 'sent_currency')
        fields = read_only_fields + read_and_write_fields

    def __init__(self, user, site, *args, **kwargs):
        self.user = user
        self.site = site
        super(CreateTransactionSerializer, self).__init__(*args, **kwargs)

    def validate_receiving_country(self, attrs, source):
        if attrs[source] not in settings.SITE_RECEIVING_COUNTRY[self.site.id]:
            raise serializers.ValidationError(constants.COUNTRY_NOT_SUPPORTED)
        return attrs

    def validate_sent_currency(self, attrs, source):
        if attrs[source] not in settings.SITE_SENDING_CURRENCY[self.site.id]:
            raise serializers.ValidationError(constants.SENT_CURRENCY_NOT_SUPPORTED)
        return attrs

    def restore_object(self, attrs, instance=None):
        recipient = models.Recipient(
            first_name=attrs['recipient'].first_name,
            last_name=attrs['recipient'].last_name,
            phone_number=attrs['recipient'].phone_number
        )
        transaction = models.Transaction(
            recipient=recipient,
            sender=self.user,
            sent_amount=attrs['sent_amount'],
            sent_currency=attrs['sent_currency'],
            receiving_country=attrs['receiving_country'],
        )

        return transaction

    def save(self, *args, **kwargs):
        with dbtransaction.atomic():
            self.object.pricing = get_current_pricing(self.site)
            self.object.exchange_rate = get_current_exchange_rate()
            self.object.generate_reference_number()
            self.object.received_amount = self.object.pricing.calculate_received_amount(
                self.object.sent_amount, self.object.receiving_country)
            self.object.recipient.save()
            self.object.recipient = models.Recipient.objects.get(id=self.object.recipient.id)
            self.object.save()
        return models.Transaction.objects.get(id=self.object.id)
