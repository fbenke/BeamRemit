from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.http import urlsafe_base64_decode

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from userena.models import UserenaSignup
from userena.utils import get_user_model, get_protocol

from beam.utils.general import log_error
from beam.utils.mails import send_sendgrid_mail

from account import constants
from account import serializers
from account.utils import AccountException, generate_aws_url

'DRF implementation of the userena.views used for Beam Accounts.'


class Signup(APIView):

    serializer_class = serializers.SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response(status=status.HTTP_201_CREATED)

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
                    return Response(status.HTTP_500_INTERNAL_SERVER_ERROR)

            # activation key expired
            else:
                return Response(
                    {'activation_key': activation_key, 'detail': constants.ACTIVATION_KEY_EXPIRED},
                    status.HTTP_400_BAD_REQUEST
                )
        # invalid key
        except UserenaSignup.DoesNotExist:
            return Response({'detail': constants.ACTIVATION_KEY_INVALID}, status.HTTP_400_BAD_REQUEST)


class ActivationRetry(APIView):

    def get(self, request, *args, **kwargs):

        activation_key = kwargs['activation_key']

        try:
            if UserenaSignup.objects.check_expired_activation(activation_key):
                user = UserenaSignup.objects.get(activation_key=activation_key).user
                new_key = UserenaSignup.objects.reissue_activation(activation_key)
                if new_key:
                    return Response({'email': user.email}, status=status.HTTP_201_CREATED)
                else:
                    log_error(
                        'ERROR - activation key could not be generated for expired key {}'.
                        format(activation_key)
                    )
                    return Response(status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(
                    {'detail': constants.ACTIVATION_KEY_NOT_EXPIRED}, status.HTTP_400_BAD_REQUEST
                )
        except UserenaSignup.DoesNotExist:
            return Response({'detail': constants.ACTIVATION_KEY_INVALID}, status.HTTP_400_BAD_REQUEST)


class ActivationResend(APIView):

    serializer_class = serializers.RequestEmailSerializer

    def post(self, request):

        try:

            serializer = self.serializer_class(data=request.DATA)

            if serializer.is_valid():

                if serializer.object.is_active:
                    raise AccountException(constants.USER_ACCOUNT_ALREADY_ACTIVATED)

                new_key = UserenaSignup.objects.reissue_activation(
                    serializer.object.userena_signup.activation_key
                )

                if new_key:
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    log_error('ERROR - activation key could not be generated for resend request for email {}'
                              .format(serializer.object.email))
                    return Response(status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AccountException as e:
            return Response({'detail': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class Signin(APIView):

    serializer_class = serializers.AuthTokenSerializer

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
        return Response()


class Email_Change(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        new_email = request.DATA.get('email', None)

        try:

            if not new_email:
                raise AccountException(constants.INVALID_PARAMETERS)
            if new_email.lower() == user.email:
                raise AccountException(constants.EMAIL_NOT_CHANGED)
            if get_user_model().objects.filter(email__iexact=new_email):
                raise AccountException(constants.EMAIL_IN_USE)

            user.userena_signup.change_email(new_email)

            return Response()

        except AccountException as e:
            return Response({'detail': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirm(APIView):

    def get(self, request, *args, **kwargs):

        confirmation_key = kwargs['confirmation_key']

        user = UserenaSignup.objects.confirm_email(confirmation_key)
        if user:
            return Response(status.HTTP_200_OK)

        return Response({'detail': constants.INVALID_PARAMETERS}, status.HTTP_400_BAD_REQUEST)


class PasswordReset(APIView):
    'DRF version of django.contrib.auth.views.password_reset'

    serializer_class = serializers.PasswordResetSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.DATA)

            if serializer.is_valid():

                if not serializer.object.is_active:
                    raise AccountException(constants.USER_ACCOUNT_DISABLED)

                serializer.save()

                return Response()

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AccountException as e:
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
            return Response()

        return Response({'detail': constants.INVALID_PARAMETERS}, status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):

        uidb64 = kwargs['uidb64']
        token = kwargs['token']

        user = self._get_user(uidb64, token)

        if not user:
            return Response({'detail': constants.INVALID_PARAMETERS})

        serializer = self.serializer_class(user=user, data=request.DATA)

        if serializer.is_valid():

            serializer.save()
            return Response()

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChange(APIView):
    serializer_class = serializers.ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):

        serializer = self.serializer_class(user=request.user, data=request.DATA)

        if serializer.is_valid():

            serializer.save()

            # issue new token for user
            request.auth.delete()
            token, _ = Token.objects.get_or_create(user=serializer.object)
            return Response({'token': token.key})

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveUpdateDestroyAPIView):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserSerializer

    def get_object(self, queryset=None):
        user = self.request.user
        return get_user_model().objects.get(id=user.id)

    def update(self, request, *args, **kwargs):
        response = super(ProfileView, self).update(request, args, kwargs)
        if response.status_code == status.HTTP_200_OK:
            response.data = {}
        return response

    def destroy(self, request, *args, **kwargs):
        '''
        customized to set active=false and delete
        token upon deletion of a user
        '''

        obj = self.get_object()
        # any pre-delete routine
        self.pre_delete(obj)

        # deactiveate users
        obj.is_active = False
        obj.save()

        # delete authentication token
        if request.auth is not None:
            request.auth.delete()

        # any post-delete routine
        self.post_delete(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateAWSLink(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):

        document_type = request.QUERY_PARAMS.get('document_type')
        key = '{}_{}'.format(document_type, self.request.user.id)
        url = generate_aws_url('PUT', key)
        return Response({'url': url}, status=status.HTTP_201_CREATED)


class UploadComplete(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            documents = request.QUERY_PARAMS.get('document')
            documents = documents.split(',')
            request.user.profile.update_model(documents)

            send_sendgrid_mail(
                subject_template_name=settings.MAIL_NOTIFY_ADMIN_DOC_UPLOADED_SUBJECT,
                email_template_name=settings.MAIL_NOTIFY_ADMIN_DOC_UPLOADED_TEXT,
                context={
                    'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                    'protocol': get_protocol(),
                    'id': request.user.profile.id
                }
            )
            return Response()
        except (AccountException, AttributeError):
            return Response(
                {'detail': constants.INVALID_PARAMETERS},
                status=status.HTTP_400_BAD_REQUEST
            )
