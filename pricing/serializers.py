from rest_framework import serializers

from pricing import models


class LimitSerializer(serializers.ModelSerializer):

    transaction_min_ghs = serializers.FloatField()
    transaction_max_ghs = serializers.FloatField()
    transaction_min_sll = serializers.FloatField()
    transaction_max_sll = serializers.FloatField()

    class Meta:
        model = models.Limit

        read_only_fields = (
            'user_limit_basic', 'user_limit_complete',
            'transaction_min', 'transaction_max', 'currency',
        )

        calculated_fields = (
            'transaction_min_ghs', 'transaction_max_ghs',
            'transaction_min_sll', 'transaction_max_sll',
        )

        fields = read_only_fields + calculated_fields
