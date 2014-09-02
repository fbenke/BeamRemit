from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

from userena import settings as userena_settings
from userena.models import UserenaSignup
from userena.utils import get_user_model

from rest_framework import serializers
from rest_framework import fields

USERNAME_RE = r'^[\.\w]+$'
PASSWORD_RE = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}$'


class SignupSerializer(serializers.Serializer):
    '''
    Serializer for creating a new user account.
    Basically ports userena.forms.SignupForm to a
    Serializer to work with Django Rest Framework.

    Validates that the requested username and e-mail is not already in use.
    Also requires the password to be entered twice.
    '''

    username = fields.RegexField(
        label=_('Username'),
        regex=USERNAME_RE,
        error_messages={
            'invalid': _('Username must contain only letters, numbers, dots and underscores.')
        }
    )

    email = fields.EmailField(
        label=_('Email'),
    )

    password1 = fields.RegexField(
        label=_('Password'),
        regex=PASSWORD_RE,
        error_messages={
            'invalid': _(
                'Password must be at least 6 characters long, contain at least one upper case letter, one lower case letter, and one numeric digit.'
            )
        }
    )

    password2 = fields.CharField(
        label=_('Repeat password')
    )

    def validate_username(self, attrs, source):
        '''
        Validate that the username is alphanumeric and is not already in use.
        Also validates that the username is not listed in
        ``USERENA_FORBIDDEN_USERNAMES`` list.
        '''

        # TODO: might be removed once we agree on dropping usernames
        # merge with logic in SignupFormOnlyEmail in that case
        try:
            get_user_model().objects.get(username__iexact=attrs['username'])
        except get_user_model().DoesNotExist:
            pass
        else:
            if userena_settings.USERENA_ACTIVATION_REQUIRED and\
               UserenaSignup.objects.filter(user__username__iexact=attrs['username'])\
               .exclude(activation_key=userena_settings.USERENA_ACTIVATED):
                raise serializers.ValidationError(
                    _('This username is already taken but not confirmed. '
                      'Please check your email for verification steps.')
                )
            raise serializers.ValidationError(_('This username is already taken.'))
        if attrs['username'].lower() in userena_settings.USERENA_FORBIDDEN_USERNAMES:
            raise serializers.ValidationError(_('This username is not allowed.'))
        return attrs

    def validate_email(self, attrs, source):
        'Validate that the e-mail address is unique.'
        if get_user_model().objects.filter(email__iexact=attrs['email']):
            if userena_settings.USERENA_ACTIVATION_REQUIRED and\
               UserenaSignup.objects.filter(user__email__iexact=attrs['email'])\
               .exclude(activation_key=userena_settings.USERENA_ACTIVATED):
                raise serializers.ValidationError(
                    _('This email is already in use but not confirmed. '
                      'Please check your email for verification steps.')
                )
            raise serializers.ValidationError(_('This email is already in use.'))
        return attrs

    def validate(self, attrs):
        '''
        Validates that the values entered into the two password fields match.
        '''

        if 'password1' in attrs and 'password2' in attrs:
            if attrs['password1'] != attrs['password2']:
                raise serializers.ValidationError(_('The two password fields didn\'t match.'))
        return attrs

    def restore_object(self, attrs, instance=None):
        '''
        Creates a new user and account. Returns the newly created user.
        '''
        if instance is not None:
            instance.update(attrs)
            return instance

        new_user = UserenaSignup.objects.create_user(
            username=attrs['username'],
            email=attrs['email'],
            password=attrs['password1'],
            active=not userena_settings.USERENA_ACTIVATION_REQUIRED,
            send_email=userena_settings.USERENA_ACTIVATION_REQUIRED
        )

        return new_user


# customized version of standard rest serializer working with email instead of username
# https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authtoken/serializers.py
class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(identification=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError(_('User account is disabled.'))
                if user.is_staff:
                    raise serializers.ValidationError(_('Login with an Admin account not supported.'))
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError(_('Unable to login with provided credentials.'))
        else:
            raise serializers.ValidationError(_('Must include "email" and "password"'))
