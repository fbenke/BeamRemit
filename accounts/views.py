from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from userena.models import UserenaSignup
from accounts import serializers

'DRF implementation of the userena.views used for Beam Accounts.'


class Signup(APIView):
    throttle_classes = (AnonRateThrottle,)
    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()

            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'token': token.key, 'id': user.id}, status.HTTP_201_CREATED
            )
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
                    # TODO: log error
                    return Response({'detail': _('User not found.')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

            # activation key expired
            else:
                return Response({'detail': _('Activation Key has expired.')})
        # invalid key
        except UserenaSignup.DoesNotExist:
            return Response({'detail': _('Invalid Key')}, status.HTTP_400_BAD_REQUEST)
