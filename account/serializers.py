from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.sites.models import Site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from hashlib import sha1 as sha_constructor
import random

from userena import settings as userena_settings
from userena.models import UserenaSignup
from userena.utils import get_user_model, get_protocol

from rest_framework import serializers
from rest_framework import fields

from beam.utils import send_mail

from account.utils import PasswordResetException
from account import models

USERNAME_RE = r'^[\.\w]+$'
PASSWORD_RE = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}$'


class PasswordSerializer(serializers.Serializer):

    password1 = fields.RegexField(
        label='Password',
        regex=PASSWORD_RE,
        error_messages={'invalid': 'Password must be at least 6 characters long, contain at least one upper case letter, one lower case letter, and one numeric digit.'}
    )

    password2 = fields.CharField(
        label='Repeat password'
    )

    def validate(self, attrs):
        '''
        Validates that the values entered into the two password fields match.
        '''

        if 'password1' in attrs and 'password2' in attrs:
            if attrs['password1'] != attrs['password2']:
                raise serializers.ValidationError('The two password fields didn\'t match.')
        return attrs


class SignupSerializer(PasswordSerializer):
    '''
    Serializer for creating a new user account.
    Basically ports userena.forms.SignupForm to a
    Serializer to work with Django Rest Framework.

    Validates that the requested username and e-mail is not already in use.
    Also requires the password to be entered twice.
    '''

    email = fields.EmailField(
        label='Email',
    )

    def validate_email(self, attrs, source):
        'Validate that the e-mail address is unique.'
        if get_user_model().objects.filter(email__iexact=attrs['email']):
            if userena_settings.USERENA_ACTIVATION_REQUIRED and\
               UserenaSignup.objects.filter(user__email__iexact=attrs['email'])\
               .exclude(activation_key=userena_settings.USERENA_ACTIVATED):
                raise serializers.ValidationError(
                    'This email is already in use but not confirmed. '
                    'Please check your email for verification steps.'
                )
            raise serializers.ValidationError('This email is already in use.')
        return attrs

    def restore_object(self, attrs, instance=None):
        ''' Generate a random username before falling back to parent signup form '''
        while True:
            username = sha_constructor(str(random.random())).hexdigest()[:5]
            try:
                get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist:
                break

        new_user = UserenaSignup.objects.create_user(
            username=username,
            email=attrs['email'],
            password=attrs['password1'],
            active=not userena_settings.USERENA_ACTIVATION_REQUIRED,
            send_email=userena_settings.USERENA_ACTIVATION_REQUIRED
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
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                if user.is_staff:
                    raise serializers.ValidationError('Login with an Admin account not supported.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')


class PasswordResetSerializer(serializers.Serializer):

    '''
    Serializer for initiating password reset.
    Basically ports django.contrib.auth.forms.PasswordResetForm to a
    Serializer to work with Django Rest Framework.
    '''

    email = fields.EmailField(label='Email')

    def restore_object(self, attrs, instance=None):
        try:
            user = get_user_model().objects.get(email__iexact=attrs['email'])
        except get_user_model().DoesNotExist:
            raise PasswordResetException('Email unknown')
        if not user.is_active:
            raise PasswordResetException('Account deleted or not activated yet')
        return user

    def save(self):

        site = Site.objects.get_current()

        context = {
            'email': self.object.email,
            'domain': site.domain,
            'site_name': site.name,
            'uid': urlsafe_base64_encode(force_bytes(self.object.pk)),
            'user': self.object,
            'token': token_generator.make_token(self.object),
            'protocol': get_protocol(),
            'without_usernames': settings.USERENA_WITHOUT_USERNAMES
        }

        send_mail(
            subject_template_name=settings.MAIL_PASSWORD_RESET_SUBJECT,
            email_template_name=settings.MAIL_PASSWORD_RESET_BODY,
            context=context,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=self.object.email,
            html_email_template_name=settings.MAIL_PASSWORD_RESET_BODY_HTML
        )


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
            raise serializers.ValidationError('Old Password is incorrect')

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
        model = get_user_model()
        read_only_fields = ('id', 'email', )
        read_and_write_fields = ('first_name', 'last_name', 'profile', )

        fields = read_only_fields + read_and_write_fields
