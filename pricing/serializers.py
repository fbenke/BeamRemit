from rest_framework import serializers

from pricing import models


class LimitSerializer(serializers.ModelSerializer):

    min_ghs = serializers.FloatField()
    max_ghs = serializers.FloatField()

    class Meta:
        model = models.Limit
        read_only_fields = ('min_gbp', 'max_gbp')

        fields = read_only_fields + ('min_ghs', 'max_ghs')
