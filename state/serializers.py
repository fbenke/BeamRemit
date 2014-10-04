from rest_framework import serializers

from state import models


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.State
        read_only_fields = ('state',)
        fields = read_only_fields
