from django.db import transaction as dbtransaction

from rest_framework import serializers

from transaction import models


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = (
            'recipient', 'amount_gbp', 'amount_btc', 'amount_ghs',
            'reference_number', 'state', 'initialized_at', 'paid_at',
            'processed_at'
        )
        fields = read_only_fields


class CreateTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = ()
        read_and_write_fields = ('amount_gbp', 'recipient')
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
            amount_gbp=attrs['amount_gbp'],
        )

        return transaction

    def validate(self, attrs):
        'make sure that the recipient is verified'
        if not self.user.profile.is_verified:
            raise serializers.ValidationError('Sender is not verified')
        return attrs

    def save(self, *args, **kwargs):
        with dbtransaction.atomic():
            self.object.recipient.save()
            self.object.recipient = models.Recipient.objects.get(id=self.object.recipient.id)
            self.object.save()
        return models.Transaction.objects.get(id=self.object.id)
