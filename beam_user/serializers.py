import re

from rest_framework import serializers

from beam_user.models import BeamUser


# TODO: Write a custom serializer in case password repeat is needed
class BeamUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = BeamUser
        fields = ('email', 'first_name', 'last_name', 'password', )
        write_only_fields = ('password', )

    def validate_first_name(self, attrs, source):
        return self._validate_name(attrs, source)

    def validate_last_name(self, attrs, source):
        return self._validate_name(attrs, source)

    def _validate_name(self, attrs, source):
        if not re.match(r'^[a-zA-Z]{4,35}$', attrs[source]):
            raise serializers.ValidationError('Name must consist of 4 - 35 letters.')
        return attrs
