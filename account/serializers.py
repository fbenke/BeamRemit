from hashlib import sha1 as sha_constructor
import random
import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from userena import settings as userena_settings
from userena.models import UserenaSignup

from rest_framework import serializers
from rest_framework import fields

from account import constants
from account import models
from account.utils import AccountException

PASSWORD_RE = r'^(?=.*\d).{8,}$'


class PasswordSerializer(serializers.Serializer):

    password1 = fields.CharField(label='Password')
    password2 = fields.CharField(label='Repeat password')

    def validate_password1(self, attrs, source):
        if not re.match(PASSWORD_RE, attrs[source]):
            raise serializers.ValidationError(constants.PASSWORD_FORMAT)
        return attrs

    def validate(self, attrs):
        '''
        Validates that the values entered into the two password fields match.
        '''

        if 'password1' in attrs and 'password2' in attrs:
            if attrs['password1'] != attrs['password2']:
                raise serializers.ValidationError(constants.PASSWORD_MISMATCH)
        return attrs


class RequestEmailSerializer(serializers.Serializer):

    email = fields.EmailField(label='Email')

    def restore_object(self, attrs, instance=None):
        try:
            user = User.objects.get(email__iexact=attrs['email'])
        except User.DoesNotExist:
            raise AccountException(constants.EMAIL_UNKNOWN)
        return user


class SignupSerializer(PasswordSerializer):
    '''
    Serializer for creating a new user account.
    Basically ports userena.forms.SignupForm to a
    Serializer to work with Django Rest Framework.

    Validates that the requested username and e-mail is not already in use.
    Also requires the password to be entered twice.
    '''
    email = fields.EmailField(label='Email')
    accepted_privacy_policy = fields.BooleanField(label='Privacy Policy accepted')

    def validate_email(self, attrs, source):
        'Validate that the e-mail address is unique.'

        if User.objects.filter(email__iexact=attrs[source]):
            if userena_settings.USERENA_ACTIVATION_REQUIRED and\
               UserenaSignup.objects.filter(user__email__iexact=attrs[source])\
               .exclude(activation_key=userena_settings.USERENA_ACTIVATED):
                raise serializers.ValidationError(constants.EMAIL_IN_USE_UNCONFIRMED)
            raise serializers.ValidationError(constants.EMAIL_IN_USE)
        return attrs

    def validate_accepted_privacy_policy(self, attrs, source):
        if not attrs[source]:
            raise serializers.ValidationError(constants.PRIVACY_POLICY_NOT_ACCEPTED)
        return attrs

    def restore_object(self, attrs, instance=None):
        ''' Generate a random username before falling back to parent signup form '''
        while True:
            username = sha_constructor(str(random.random())).hexdigest()[:5]
            try:
                User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                break

        new_user = UserenaSignup.objects.create_user(
            username=username,
            email=attrs['email'],
            password=attrs['password1'],
            active=not userena_settings.USERENA_ACTIVATION_REQUIRED,
            # this will be done manually in the next step to allow more flexibiliy
            send_email=False
        )

        return new_user

    def save(self, *args, **kwargs):
        '''
        Overwritten, because the actual save has been done in restore_object.
        This helps just with verifying, that restore_object actually returned a
        user object
        '''
        return self.object


class AuthTokenSerializer(serializers.Serializer):
    '''
    customized version of standard rest serializer working
    with email instead of username

    see: https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authtoken/serializers.py
    '''

    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(identification=email, password=password)
            if user:

                if user.is_staff:
                    raise serializers.ValidationError(constants.ADMIN_ACCOUNT)

                if user.profile.account_deactivated:
                    raise serializers.ValidationError(constants.USER_ACCOUNT_DISABLED)

                if not user.is_active:
                    raise serializers.ValidationError(constants.USER_ACCOUNT_NOT_ACTIVATED_YET)

                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError(constants.SIGNIN_WRONG_CREDENTIALS)
        else:
            raise serializers.ValidationError(constants.SIGNIN_MISSING_CREDENTIALS)


class SetPasswordSerializer(PasswordSerializer):

    '''
    Serializer for resetting password without entering the old one.
    Basically ports django.contrib.auth.forms.SetPasswordForm to a
    Serializer to work with Django Rest Framework.
    '''

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordSerializer, self).__init__(*args, **kwargs)

    def restore_object(self, attrs, instance=None):
        self.user.set_password(attrs['password1'])
        return self.user


class ChangePasswordSerializer(SetPasswordSerializer):
    '''
    Serializer for resetting password by entering the old one.
    Basically ports django.contrib.auth.forms.PasswordChangeForm to a
    Serializer to work with Django Rest Framework.
    '''

    old_password = serializers.CharField(label='Old password')

    def validate_old_password(self, attrs, source):

        old_password = attrs[source]
        if not self.user.check_password(old_password):
            raise serializers.ValidationError(constants.PASSWORD_OLD_INCORRECT)

        return attrs


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BeamProfile
        read_only_fields = ()
        read_and_write_fields = (
            'date_of_birth', 'street', 'post_code', 'city', 'country'
        )

        fields = read_only_fields + read_and_write_fields


class UserSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(many=False)

    class Meta:
        model = User
        read_only_fields = ('email', )
        read_and_write_fields = ('first_name', 'last_name', 'profile')

        fields = read_only_fields + read_and_write_fields
