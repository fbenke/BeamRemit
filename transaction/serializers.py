from django.db import transaction as dbtransaction

from rest_framework import serializers

from transaction import models


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transaction


class CreateTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = ()
        read_and_write_fields = ('amount_btc', 'amount_ghs', 'recipient')
        fields = read_only_fields + read_and_write_fields

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(CreateTransactionSerializer, self).__init__(*args, **kwargs)

    def restore_object(self, attrs, instance=None):
        recipient = models.Recipient(
            name=attrs['recipient'].name,
            phone_number=attrs['recipient'].phone_number,
            notification_email=attrs['recipient'].notification_email
        )
        transaction = models.Transaction(
            recipient=recipient,
            sender=self.user,
            amount_btc=attrs['amount_btc'],
            amount_ghs=attrs['amount_ghs']
        )

        return transaction

    def save(self, *args, **kwargs):
        with dbtransaction.atomic():
            self.object.recipient.save()
            self.object.recipient = models.Recipient.objects.get(id=self.object.recipient.id)
            self.object.save()


class PricingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Pricing
        read_and_write_fields = ('markup', 'ghs_usd')
        read_only_fields = ('id', 'start', 'end',)
        fields = read_only_fields + read_and_write_fields

    def validate_markup(self, attrs, source):
        if not (0.0 <= attrs[source] <= 1.0):
            raise serializers.ValidationError(
                'markup has to be a value between 0 and 1')
        return attrs
