from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from userena.models import UserenaSignup

from accounts import serializers

from beam.utils import log_error

'DRF implementation of the userena.views used for Beam Accounts.'


class Signup(APIView):
    throttle_classes = (AnonRateThrottle,)
    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response({'detail': 'success'}, status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Activation(APIView):
    throttle_classes = (AnonRateThrottle,)

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
    throttle_classes = (AnonRateThrottle,)

    def get(self, request, *args, **kwargs):

        activation_key = kwargs['activation_key']

        try:
            if UserenaSignup.objects.check_expired_activation(activation_key):
                new_key = UserenaSignup.objects.reissue_activation(activation_key)
                if new_key:
                    return Response({'detail': 'success'}, status.HTTP_201_CREATED)
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
    throttle_classes = (AnonRateThrottle,)
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
    throttle_classes = (AnonRateThrottle,)

    def post(self, request):
        if request.auth is not None:
            request.auth.delete()
            return Response({'status': 'success'})
        return Response()
