from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


from beam_user import serializers
from beam_user.models import BeamUser
from beam_user.permissions import IsOwner


class CreateUserView(APIView):
    throttle_classes = (AnonRateThrottle,)
    serializer_class = serializers.BeamUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'token': token.key, 'id': user.id}, status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
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


class EditUserView(generics.UpdateAPIView):
    serializer_class = serializers.BeamUserSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return BeamUser.objects.filter(is_active=True)


class RetrieveUserView(generics.RetrieveAPIView):
    serializer_class = serializers.BeamUserSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return BeamUser.objects.filter(is_active=True)


class DeleteUserView(generics.DestroyAPIView):
    serializer_class = serializers.BeamUserSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return BeamUser.objects.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):

        response = super(generics.DestroyAPIView, self).destroy(
            request=request, *args, **kwargs
        )
        
        if request.auth is not None:
            request.auth.delete()
        return response


@api_view(['POST'])
def logout(request):
    if request.auth is not None:
        request.auth.delete()
    return Response({'status': 'success'})
