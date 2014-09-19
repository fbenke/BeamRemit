from rest_framework import serializers

from pricing import models


class PricingSerializer(serializers.ModelSerializer):

    def exchange_rate(self, obj):
        return obj.gbp_ghs * (1 - obj.markup)

    gbp_ghs = serializers.SerializerMethodField('exchange_rate')

    class Meta:
        model = models.Pricing
        fields = ('id', 'gbp_ghs', 'fee')
