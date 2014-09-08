from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.http import urlsafe_base64_decode

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from userena.models import UserenaSignup
from userena.utils import get_user_model

from beam.utils import log_error

from accounts import serializers
from accounts.utils import EmailChangeException, PasswordResetException

'DRF implementation of the userena.views used for Beam Accounts.'

RESPONSE_SUCCESS = 'Success'
RESPONSE_INVD_PARAM = 'Invalid Parameters'


class Signup(APIView):

    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response({'detail': RESPONSE_SUCCESS}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Activation(APIView):

    def get(self, request, *args, **kwargs):

        activation_key = kwargs['activation_key']

        try:
            if not UserenaSignup.objects.check_expired_activation(activation_key):

                user = UserenaSignup.objects.activate_user(activation_key)

                # account successfully activated
                if user:
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({'token': token.key, 'id': user.id}, status.HTTP_200_OK)

                else:
                    log_error(
                        'ERROR - User for activation key {} could not be found'.
                        format(activation_key)
                    )
                    return Response({'detail': 'User not found.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # activation key expired
            else:
                return Response(
                    {'activation_key': activation_key,
                     'detail': 'Activation Key has expired.'},
                    status.HTTP_200_OK
                )
        # invalid key
        except UserenaSignup.DoesNotExist:
            return Response({'detail': 'Invalid Key'}, status.HTTP_400_BAD_REQUEST)


class ActivationRetry(APIView):

    def get(self, request, *args, **kwargs):

        activation_key = kwargs['activation_key']

        try:
            if UserenaSignup.objects.check_expired_activation(activation_key):
                new_key = UserenaSignup.objects.reissue_activation(activation_key)
                if new_key:
                    return Response({'detail': RESPONSE_SUCCESS}, status.HTTP_201_CREATED)
                else:
                    log_error(
                        'ERROR - activation key could not be generated for expired key {}'.
                        format(activation_key)
                    )
                    return Response(
                        {'detail': 'Key could not be generated.'},
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {'detail': 'Key is not expired.'},
                    status.HTTP_400_BAD_REQUEST
                )
        except UserenaSignup.DoesNotExist:
            return Response({'detail': 'Invalid Key'}, status.HTTP_400_BAD_REQUEST)


class Signin(APIView):

    serializer_class = serializers.AuthTokenSerializer
    model = Token

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            authenticated_user = serializer.object['user']
            token, created = Token.objects.get_or_create(user=authenticated_user)
            return Response(
                {'token': token.key, 'id': authenticated_user.id})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Signout(APIView):

    def post(self, request):
        if request.auth is not None:
            request.auth.delete()
            return Response({'detail': RESPONSE_SUCCESS})
        return Response()


class Email_Change(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request):
        user = request.user
        new_email = request.DATA.get('email', None)

        try:

            if not new_email:
                raise EmailChangeException(RESPONSE_INVD_PARAM)
            if new_email.lower() == user.email:
                raise EmailChangeException('You are already known under this email.')
            if get_user_model().objects.filter(email__iexact=new_email):
                raise EmailChangeException('This email is already in use. Please supply a different email.')

            user.userena_signup.change_email(new_email)

            return Response({'detail': RESPONSE_SUCCESS})

        except EmailChangeException as e:
            return Response({'detail': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirm(APIView):

    def get(self, request, *args, **kwargs):

        confirmation_key = kwargs['confirmation_key']

        user = UserenaSignup.objects.confirm_email(confirmation_key)
        if user:
            return Response({'detail': 'Success'}, status.HTTP_200_OK)

        return Response({'detail': RESPONSE_INVD_PARAM}, status.HTTP_400_BAD_REQUEST)


class PasswordReset(APIView):
    'DRF version of django.contrib.auth.views.password_reset'

    serializer_class = serializers.PasswordResetSerializer

    def post(self, request):
        email = request.DATA.get('email', None)

        try:
            if not email:
                raise PasswordResetException(RESPONSE_INVD_PARAM)

            serializer = self.serializer_class(data=request.DATA)

            if serializer.is_valid():

                serializer.save()

                return Response({'detail': RESPONSE_SUCCESS})

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except PasswordResetException as e:

            return Response({'detail': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirm(APIView):
    'DRF version of django.contrib.auth.views.password_reset_confirm'

    serializer_class = serializers.SetPasswordSerializer

    def _get_user(self, uidb64, token):

        try:
            uid = urlsafe_base64_decode(uidb64)
            user = get_user_model().objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):
            return user

        return None

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs['uidb64']
        token = kwargs['token']

        if self._get_user(uidb64, token):
            return Response({'detail': RESPONSE_SUCCESS})

        return Response({'detail': RESPONSE_INVD_PARAM})

    def post(self, request, *args, **kwargs):

        uidb64 = kwargs['uidb64']
        token = kwargs['token']

        user = self._get_user(uidb64, token)

        if not user:
            return Response({'detail': RESPONSE_INVD_PARAM})

        serializer = self.serializer_class(user, user, request.DATA)

        if serializer.is_valid():

            serializer.save()
            return Response({'detail': RESPONSE_SUCCESS})

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
