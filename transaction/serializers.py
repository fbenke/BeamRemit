from django.conf import settings
from django.db import transaction as dbtransaction

from rest_framework import serializers
from rest_framework import fields

from transaction import models
from transaction import constants


class TransactionSerializer(serializers.ModelSerializer):

    received_currency = fields.FloatField()

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = (
            'id', 'recipient', 'amount_gbp', 'amount_btc', 'received_amount',
            'reference_number', 'state', 'initialized_at', 'paid_at', 'processed_at'
        )
        fields = read_only_fields + ('received_currency',)


class CreateTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = ()
        read_and_write_fields = ('recipient', 'receiving_country', 'amount_gbp')
        fields = read_only_fields + read_and_write_fields

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(CreateTransactionSerializer, self).__init__(*args, **kwargs)

    def validate_receiving_country(self, attrs, source):
        if attrs[source] not in settings.RECEIVING_COUNTRIES:
            raise serializers.ValidationError(constants.COUNTRY_NOT_SUPPORTED)
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
            amount_gbp=attrs['amount_gbp'],
            receiving_country=attrs['receiving_country']
        )

        return transaction

    def save(self, *args, **kwargs):
        with dbtransaction.atomic():
            self.object.recipient.save()
            self.object.recipient = models.Recipient.objects.get(id=self.object.recipient.id)
            self.object.save()
        return models.Transaction.objects.get(id=self.object.id)
