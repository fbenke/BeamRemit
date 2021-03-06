from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import transaction as dbtransaction
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from userena import settings as userena_settings
from userena.models import UserenaSignup
from userena.utils import generate_sha1, get_datetime_now

from beam.utils.log import log_error
from beam.utils import mails
from beam.utils.angular_requests import get_site_by_request

from account import constants
from account import serializers
from account.models import BeamProfile as Profile
from account.utils import AccountException, generate_aws_upload

from pricing.models import get_current_limit

from beam.utils.ip_blocking import country_blocked, is_tor_node,\
    get_client_ip, HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS

'DRF implementation of the userena.views used for Beam Accounts.'


def send_activation_email(user, request, activation_key=None):

    if not activation_key:
        activation_key = user.userena_signup.activation_key

    context = {
        'user': user,
        'protocol': settings.PROTOCOL,
        'activation_days': userena_settings.USERENA_ACTIVATION_DAYS,
        'activation_link': settings.MAIL_ACTIVATION_URL.format(activation_key),
        'site': get_site_by_request(request)
    }

    mails.send_mail(
        subject_template_name=settings.MAIL_ACTIVATION_SUBJECT,
        email_template_name=settings.MAIL_ACTIVATION_TEXT,
        html_email_template_name=settings.MAIL_ACTIVATION_HTML,
        to_email=user.email,
        from_email=settings.BEAM_MAIL_ADDRESS,
        context=context
    )


def reissue_activation(activation_key):
    '''
    Rewritten version of UserenaSignup.objects.reissue_activation()
    to customize the sent email
    '''

    try:
        userena = UserenaSignup.objects.get(activation_key=activation_key)
    except UserenaSignup.objects.model.DoesNotExist:
        return None
    try:
        salt, new_activation_key = generate_sha1(userena.user.username)
        userena.activation_key = new_activation_key
        userena.save(using=UserenaSignup.objects._db)
        userena.user.date_joined = get_datetime_now()
        userena.user.save(using=UserenaSignup.objects._db)
        return new_activation_key
    except Exception:
        return None


class Signup(APIView):

    serializer_class = serializers.SignupSerializer

    def post(self, request):

        # block countries we are not licensed to operate in and tor clients
        client_ip = get_client_ip(request)

        if country_blocked(request, client_ip) or is_tor_node(client_ip):
            return Response(status=HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

        serializer = self.serializer_class(data=request.DATA)

        if serializer.is_valid():

            user = serializer.save()

            if user:
                # store site the user signed up at
                user.profile.signup_site_id = get_site_by_request(self.request).id
                user.profile.save()

                send_activation_email(user, request)

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

                new_activation_key = reissue_activation(activation_key)

                if new_activation_key:

                    send_activation_email(user, request, new_activation_key)

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

                # handle deactivated account
                if serializer.object.profile.account_deactivated:

                    raise AccountException(constants.USER_ACCOUNT_DISABLED)

                new_activation_key = reissue_activation(serializer.object.userena_signup.activation_key)

                if new_activation_key:

                    send_activation_email(serializer.object, request, new_activation_key)

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

        # block countries we are not licensed to operate in and tor clients
        client_ip = get_client_ip(request)

        if country_blocked(request, client_ip) or is_tor_node(client_ip):
            return Response(status=HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

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
            if User.objects.filter(email__iexact=new_email):
                raise AccountException(constants.EMAIL_IN_USE)

            # the following is a rewritten version of user.userena_signup.change_email(new_email)
            user.userena_signup.email_unconfirmed = new_email
            salt, hash = generate_sha1(user.username)
            user.userena_signup.email_confirmation_key = hash
            user.userena_signup.email_confirmation_key_created = get_datetime_now()
            user.userena_signup.save()

            # the purpose is rewriting the following part where the emails are sent out
            context = {
                'user': user,
                'protocol': settings.PROTOCOL,
                'email_change_link': settings.MAIL_EMAIL_CHANGE_CONFIRM_URL.format(user.userena_signup.email_confirmation_key),
                'site': get_site_by_request(request)
            }

            # mail to new email account
            mails.send_mail(
                subject_template_name=settings.MAIL_CHANGE_EMAIL_NEW_SUBJECT,
                email_template_name=settings.MAIL_CHANGE_EMAIL_NEW_TEXT,
                html_email_template_name=settings.MAIL_CHANGE_EMAIL_NEW_HTML,
                to_email=user.userena_signup.email_unconfirmed,
                from_email=settings.BEAM_MAIL_ADDRESS,
                context=context
            )

            context['support'] = settings.BEAM_SUPPORT
            context['new_email'] = user.userena_signup.email_unconfirmed

            # mail to old email account
            mails.send_mail(
                subject_template_name=settings.MAIL_CHANGE_EMAIL_OLD_SUBJECT,
                email_template_name=settings.MAIL_CHANGE_EMAIL_OLD_TEXT,
                html_email_template_name=settings.MAIL_CHANGE_EMAIL_OLD_HTML,
                to_email=user.email,
                from_email=settings.BEAM_MAIL_ADDRESS,
                context=context
            )
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

    serializer_class = serializers.RequestEmailSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.DATA)

            if serializer.is_valid():

                if serializer.object.profile.account_deactivated:
                    raise AccountException(constants.USER_ACCOUNT_DISABLED)

                if not serializer.object.is_active:
                    raise AccountException(constants.USER_ACCOUNT_NOT_ACTIVATED_YET)

                uid = urlsafe_base64_encode(force_bytes(serializer.object.pk))
                token = token_generator.make_token(serializer.object)

                context = {
                    'email': serializer.object.email,
                    'site': get_site_by_request(request),
                    'password_reset_link': settings.MAIL_PASSWORD_RESET_URL.format(uid, token),
                    'first_name': serializer.object.first_name,
                    'protocol': settings.PROTOCOL,
                }

                mails.send_mail(
                    subject_template_name=settings.MAIL_PASSWORD_RESET_SUBJECT,
                    email_template_name=settings.MAIL_PASSWORD_RESET_TEXT,
                    html_email_template_name=settings.MAIL_PASSWORD_RESET_HTML,
                    context=context,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_email=serializer.object.email
                )

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
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
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
        return User.objects.get(id=user.id)

    def update(self, request, *args, **kwargs):

        with dbtransaction.atomic():

            response = super(ProfileView, self).update(request, args, kwargs)

            if response.status_code == status.HTTP_200_OK:

                changed_params = request.DATA.keys() + request.DATA.get('profile').keys()

                passport_params = ['first_name', 'last_name', 'date_of_birth']
                por_params = ['street', 'post_code', 'city', 'country']

                # need to reupload identification doc
                if ((list(set(passport_params) & set(changed_params))) and
                        request.user.profile.identification_state != Profile.EMPTY):
                    request.user.profile.update_document_state(Profile.IDENTIFICATION, Profile.EMPTY)
                    request.user.profile.identification_issue_date = None
                    request.user.profile.identification_expiry_date = None
                    request.user.profile.identification_number = ''
                    request.user.profile.save()

                # need to reupload proof of residence
                if ((list(set(por_params) & set(changed_params))) and
                        request.user.profile.proof_of_residence_state != Profile.EMPTY):
                    request.user.profile.update_document_state(Profile.PROOF_OF_RESIDENCE, Profile.EMPTY)

                # clear response data
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


class GenerateAWSUpload(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):

        document_type = request.QUERY_PARAMS.get('documenttype', None)
        content_type = request.QUERY_PARAMS.get('contenttype', None)

        # check if parameters are complete
        if (not document_type or not content_type or document_type
                not in Profile.DOCUMENT_TYPES):

            return Response({'detail': constants.INVALID_PARAMETERS},
                            status=status.HTTP_400_BAD_REQUEST)

        # allow upload only if the profile information is complete
        if not request.user.profile.information_complete:

            log_error('ERROR Generate AWS Link - User {} has not completed their profile'.
                      format(request.user.id))

            return Response(
                {'detail': constants.USER_PROFILE_INCOMPLETE},
                status=status.HTTP_400_BAD_REQUEST)

        # allow upload only if the current status is 'declied' or 'empty'
        if request.user.profile.get_document_state(document_type)\
                not in (Profile.EMPTY, Profile.FAILED):

            log_error('ERROR Generate AWS Link - Unexpected Request from user id: {}'.
                      format(request.user.id))

            return Response(
                {'detail': constants.DOCUMENT_ALREADY_UPLOADED},
                status=status.HTTP_400_BAD_REQUEST)

        key = '{}_{}'.format(document_type, request.user.id)
        upload_params = generate_aws_upload(key, content_type)
        return Response(upload_params, status=status.HTTP_201_CREATED)


class UploadComplete(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            document = request.DATA.get('document')
            profile = request.user.profile

            # allow state change only if the profile information is complete
            if not profile.information_complete:

                log_error('ERROR Document Upload Complete - User {} has not completed their profile'.
                          format(request.user.id))

                return Response(
                    {'detail': constants.USER_PROFILE_INCOMPLETE},
                    status=status.HTTP_400_BAD_REQUEST)

            # allow state change only if the current status is 'declied' or 'empty'
            if profile.get_document_state(document)\
                    not in (Profile.EMPTY, Profile.FAILED):

                log_error('ERROR Document Upload Complete - Unexpected Request from user id: {}'.
                          format(request.user.id))

                return Response(
                    {'detail': constants.DOCUMENT_ALREADY_UPLOADED},
                    status=status.HTTP_400_BAD_REQUEST)

            if document == Profile.IDENTIFICATION:

                issue = request.DATA.get('issue', None)
                expiry = request.DATA.get('expiry', None)
                number = request.DATA.get('number', None)

                if not issue or not expiry or not number:
                    raise AccountException

                profile.identification_issue_date = issue
                profile.identification_expiry_date = expiry
                profile.identification_number = number

            profile.update_document_state(document, Profile.UPLOADED)

            # notify admins that a document needs to be verified
            mails.send_mail(
                subject_template_name=settings.MAIL_NOTIFY_ADMIN_DOC_UPLOADED_SUBJECT,
                email_template_name=settings.MAIL_NOTIFY_ADMIN_DOC_UPLOADED_TEXT,
                context={
                    'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                    'protocol': settings.PROTOCOL,
                    'id': profile.id,
                    'document': Profile.DOCUMENT_VERBAL[document],
                    'site_name': Site.objects.get_current().name
                },
                to_email=mails.get_admin_mail_addresses()
            )

            return Response()

        except (AccountException, AttributeError, KeyError):
            return Response(
                {'detail': constants.INVALID_PARAMETERS},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerificationStatus(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        data = request.user.profile.get_document_states()
        data['information_complete'] = request.user.profile.information_complete
        return Response(data)


class AccountLimits(APIView):

    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):

        site = get_site_by_request(self.request)

        todays_vol = request.user.profile.todays_transaction_volume(site)

        limit = get_current_limit(site)

        if request.user.profile.documents_verified:
            account_limit = limit.user_limit_complete
            can_extend = False
        else:
            account_limit = limit.user_limit_basic
            can_extend = True

        data = {
            'today': todays_vol,
            'limit': account_limit,
            'currency': settings.SITE_SENDING_CURRENCY[site.id],
            'can_extend': can_extend
        }
        return Response(data)
