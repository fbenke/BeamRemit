from django.db import transaction as dbtransaction

from django.contrib.auth import authenticate

import re

from rest_framework import serializers

from beam_user.models import BeamUser


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

    def validate_password(self, attrs, source):
        if not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}$', attrs[source]):
            raise serializers.ValidationError(
                'Password must be at least 6 characters long, contain at least'
                'one upper case letter, one lower case letter, and one numeric digit.'
            )
        return attrs

    def save(self, force_insert=False, force_update=False, using=None):
        with dbtransaction.atomic():
            user = super(BeamUserSerializer, self).save()
            user.set_password(user.password)
            user.save()
        return user


# customized version of standard rest serializer working with email instead of username
# https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authtoken/serializers.py
class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                if user.is_admin:
                    raise serializers.ValidationError('Login with an Admin account not supported.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')
