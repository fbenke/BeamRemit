from rest_framework import generics
from rest_framework.throttling import AnonRateThrottle

from beam_user import serializers
from beam_user.models import BeamUser


class CreateUserView(generics.CreateAPIView):
    serializer_class = serializers.BeamUserSerializer
    throttle_classes = (AnonRateThrottle,)


class RetrieveUserView(generics.RetrieveAPIView):
    serializer_class = serializers.BeamUserSerializer
    throttle_classes = (AnonRateThrottle,)

    def get_queryset(self):
        return BeamUser.objects.filter(is_active=True)
