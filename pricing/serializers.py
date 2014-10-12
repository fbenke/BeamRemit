from rest_framework import serializers

from pricing import models


class LimitSerializer(serializers.ModelSerializer):

    max_ghs = serializers.FloatField()

    class Meta:
        model = models.Limit
        read_only_fields = ('max_gbp',)

        fields = read_only_fields + ('max_ghs',)
