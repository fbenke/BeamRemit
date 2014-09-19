from rest_framework import serializers

from pricing import models


class PricingSerializer(serializers.ModelSerializer):

    def calculate_exchange_rate(self, obj):
        return obj.gbp_ghs * (1 - obj.markup)

    exchange_rate = serializers.SerializerMethodField('calculate_exchange_rate')

    class Meta:
        model = models.Pricing
        fields = ('id', 'exchange_rate', 'fee')
