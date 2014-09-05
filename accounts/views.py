from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from userena.models import UserenaSignup
from userena.utils import get_user_model

from accounts import serializers

from beam.utils import log_error, EmailChangeException

'DRF implementation of the userena.views used for Beam Accounts.'


class Signup(APIView):

    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        try:
            if serializer.is_valid():
                user = serializer.save()
                if user:
                    return Response({'status': 'success'}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as v:
            return Response(repr(v), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                    return Response({'detail': _('User not found.')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # activation key expired
            else:
                return Response(
                    {'activation_key': activation_key,
                     'detail': _('Activation Key has expired.')},
                    status.HTTP_200_OK
                )
        # invalid key
        except UserenaSignup.DoesNotExist:
            return Response({'detail': _('Invalid Key')}, status.HTTP_400_BAD_REQUEST)


class ActivationRetry(APIView):

    def get(self, request, *args, **kwargs):

        activation_key = kwargs['activation_key']

        try:
            if UserenaSignup.objects.check_expired_activation(activation_key):
                new_key = UserenaSignup.objects.reissue_activation(activation_key)
                if new_key:
                    return Response({'status': 'success'}, status.HTTP_201_CREATED)
                else:
                    log_error(
                        'ERROR - activation key could not be generated for expired key {}'.
                        format(activation_key)
                    )
                    return Response(
                        {'detail': _('Key could not be generated.')},
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {'detail': _('Key is not expired.')},
                    status.HTTP_400_BAD_REQUEST
                )
        except UserenaSignup.DoesNotExist:
            return Response({'detail': _('Invalid Key')}, status.HTTP_400_BAD_REQUEST)


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
            return Response({'status': 'success'})
        return Response()


class Email_Change(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request):
        user = request.user
        new_email = request.DATA.get('email', None)

        try:

            if not new_email:
                raise EmailChangeException({'detail': _('Invalid parameters')})
            if new_email.lower() == user.email:
                raise EmailChangeException({'detail': _('You are already known under this email.')})
            if get_user_model().objects.filter(email__iexact=new_email):
                raise EmailChangeException({'detail': _('This email is already in use. Please supply a different email.')})

            user.userena_signup.change_email(new_email)

            return Response({'status': 'success'})

        except EmailChangeException as e:
            return Response(e.args[0], status=status.HTTP_400_BAD_REQUEST)


class Email_Confirm(APIView):

    def get(self, request, *args, **kwargs):

        confirmation_key = kwargs['confirmation_key']

        user = UserenaSignup.objects.confirm_email(confirmation_key)
        if user:
            return Response({'status': 'success'}, status.HTTP_200_OK)

        return Response({'detail': 'invalid'}, status.HTTP_400_BAD_REQUEST)
