from rest_framework import serializers

from transaction import models


class RecipientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Recipient
        read_only_fields = ()
        read_and_write_fields = ('name', 'phone_number', 'notification_email')
        fields = read_only_fields + read_and_write_fields


class TransactionSerializer(serializers.ModelSerializer):

    recipient = RecipientSerializer(many=False, required=True)

    class Meta:
        model = models.Transaction
        depth = 1
        read_only_fields = (
            'initialized_at', 'paid_at', 'processed_at', 'declined_at', 'cancelled_at',
            'pricing', 'state', 'amount_btc', 'amount_ghs'
        )
        read_and_write_fields = ('recipient', 'reference_number')
        fields = read_only_fields + read_and_write_fields

    def restore_object(self, attrs, instance=None):
        transaction = super(TransactionSerializer, self).__init__(attrs, instance)
        transaction.sender.id = 2
        return transaction


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
