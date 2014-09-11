from rest_framework import serializers

from pricing import models


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
