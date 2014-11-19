from rest_framework import serializers

from pricing import models


class LimitSerializer(serializers.ModelSerializer):

    transaction_min_receiving = serializers.FloatField()
    transaction_max_receiving = serializers.FloatField()
    sending_currency = serializers.FloatField()
    receiving_currency = serializers.FloatField()

    class Meta:
        model = models.Limit

        read_only_fields = (
            'user_limit_basic', 'user_limit_complete',
            'transaction_min', 'transaction_max',
        )

        calculated_fields = (
            'transaction_min_receiving', 'transaction_max_receiving',
            'sending_currency', 'receiving_currency'
        )

        fields = read_only_fields + calculated_fields
