from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from accounts import serializers


class SignupView(APIView):
    throttle_classes = (AnonRateThrottle,)
    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()

            # TODO: do we need that signal?
            # userena_signals.signup_complete.send(
            # 	sender=None, user=user
            # )

            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'token': token.key, 'id': user.id}, status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
