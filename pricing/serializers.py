from rest_framework import serializers

from pricing import models


class LimitSerializer(serializers.ModelSerializer):

    user_limit_basic_usd = serializers.FloatField()
    user_limit_complete_usd = serializers.FloatField()
    transaction_min_usd = serializers.FloatField()
    transaction_max_usd = serializers.FloatField()
    transaction_min_ghs = serializers.FloatField()
    transaction_max_ghs = serializers.FloatField()
    transaction_min_sll = serializers.FloatField()
    transaction_max_sll = serializers.FloatField()

    class Meta:
        model = models.Limit

        read_only_fields = (
            'user_limit_basic_gbp', 'user_limit_complete_gbp',
            'transaction_min_gbp', 'transaction_max_gbp'
        )

        calculated_fields = (
            'user_limit_basic_usd', 'user_limit_complete_usd',
            'transaction_min_usd', 'transaction_max_usd',
            'transaction_min_ghs', 'transaction_max_ghs',
            'transaction_min_sll', 'transaction_max_sll'
        )

        fields = read_only_fields + calculated_fields
