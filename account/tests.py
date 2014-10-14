from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.core.urlresolvers import reverse
from django.core import mail as mailbox
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_framework import status

from userena.utils import get_user_model

from datetime import timedelta

from beam.tests import BeamAPITestCase
from account import constants
from account.models import BeamProfile as Profile


class AccountTests(BeamAPITestCase):

    url_signin = reverse('account:signin')
    url_singout = reverse('account:signout')
    url_email_change = reverse('account:email_change')
    url_password_reset = reverse('account:password_reset')
    url_password_change = reverse('account:password_change')
    url_activate_resend = reverse('account:activate_resend')
    url_aws_upload = reverse('account:aws')
    url_upload_complete = reverse('account:upload_complete')
    url_verification_status = reverse('account:verification_status')

    plain_url_activate_retry = 'account:activate_retry'
    plain_url_email_change_confirm = 'account:email_confirm'
    plain_url_password_reset_confirm = 'account:password_reset_confirm'

    def _generate_password_reset_confirmation_key(self, id):
        user = get_user_model().objects.get(id=id)
        return urlsafe_base64_encode(force_bytes(user.pk)), token_generator.make_token(user)

    def test_signup(self):

        no_emails = len(mailbox.outbox)

        email = self.emails.next()
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert that mail was sent
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get activation key and send activate get request
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))

        # check if mail contains correct link
        self.assertTrue(settings.MAIL_ACTIVATION_URL.format(activation_key) in mailbox.outbox[0].body)
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_signup_validation_empty(self):
        'empty post'
        response = self.client.post(self.url_signup, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_validation_incomplete(self):
        'incomplete post'
        data = {
            'email': self.emails.next(),
            'password1': self.password
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password2'][0], 'This field is required.')

    def test_signup_validation_password_mismatch(self):
        'password mismatch'
        data = {
            'email': self.emails.next(),
            'password1': self.password,
            'password2': self.password[1:]
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.PASSWORD_MISMATCH)

    def test_signup_validation_unconfirmed_mail(self):
        'duplicate mail'
        email = self.emails.next()
        self._create_user(email=email)
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], constants.EMAIL_IN_USE_UNCONFIRMED)

    def test_signup_validation_duplicate_mail(self):
        'duplicate mail'
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], constants.EMAIL_IN_USE)

    def test_activation_invalid_key(self):
        url_activate = reverse(self.plain_url_activate, args=('invalidkey',))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_INVALID)

    def test_activation_expired_key(self):
        email = self.emails.next()
        self._create_user(email=email)

        # manipulate db so that activation key is expired
        user = get_user_model().objects.get(email__iexact=email)
        user.date_joined = timezone.now() - timedelta(settings.USERENA_ACTIVATION_DAYS)
        user.save()

        # get activation key and send activate get request
        activation_key = user.userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['activation_key'] is not None)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_EXPIRED)

        # request a new activation key
        url_activate_retry = reverse(self.plain_url_activate_retry, args=(activation_key,))
        response = self.client.get(url_activate_retry)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # activate account with new activation key
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))

        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_activation_retry_invalid_key(self):
        url_activate_retry = reverse(self.plain_url_activate_retry, args=('invalidkey',))
        response = self.client.get(url_activate_retry)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_INVALID)

    def test_activation_retry_valid_key(self):
        email = self.emails.next()
        self._create_user(email)
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate_retry = reverse(self.plain_url_activate_retry, args=(activation_key,))
        response = self.client.get(url_activate_retry)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_NOT_EXPIRED)

    def test_activation_resend(self):
        email = self.emails.next()
        self._create_user(email=email)
        response = self.client.post(self.url_activate_resend, {"email": email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_activation_resend_unknown_email(self):
        email = self.emails.next()
        response = self.client.post(self.url_activate_resend, {"email": email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_UNKNOWN)

    def test_signin(self):
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_signin_validation_empty(self):
        response = self.client.post(self.url_signin, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'This field is required.')
        self.assertEqual(response.data['email'][0], 'This field is required.')

    def test_signin_wrong_credentials(self):
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password[1:]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.SIGNIN_WRONG_CREDENTIALS)

    def test_singin_without_activation(self):
        email = self.emails.next()
        self._create_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.USER_ACCOUNT_DISABLED)

    def test_signout(self):
        token, _ = self._create_activated_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_singout)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_change(self):
        old_email = self.emails.next()
        token, _ = self._create_activated_user(email=old_email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        no_emails = len(mailbox.outbox)
        new_mail = self.emails.next()
        response = self.client.post(self.url_email_change, {'email': new_mail})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that two mails were sent
        self.assertEqual(len(mailbox.outbox), no_emails + 2)

        # check if corresponding database fields exist
        user = get_user_model().objects.get(email__iexact=old_email)
        self.assertEqual(user.userena_signup.email_unconfirmed, new_mail)

        confirmation_key = user.userena_signup.email_confirmation_key

        url_email_change_confirm = reverse(self.plain_url_email_change_confirm, args=(confirmation_key,))
        response = self.client.get(url_email_change_confirm)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # verify that new email address is active and old no longer in use
        self.assertIsNotNone(get_user_model().objects.get(email__iexact=new_mail))
        with self.assertRaises(get_user_model().DoesNotExist):
            get_user_model().objects.get(email__iexact=old_email)

    def test_email_change_failure_empty(self):
        token, _ = self._create_activated_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_email_change, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_email_change_failure_same_mail(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_email_change, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_NOT_CHANGED)

    def test_email_change_failure_existing_mail(self):
        # create a user with email
        email = self.emails.next()
        self._create_activated_user(email)
        # create another user
        token, _ = self._create_activated_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        # try to change to email of first user
        response = self.client.post(self.url_email_change, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_IN_USE)

    def test_email_change_confirm_failure(self):
        url_email_change_confirm = reverse(self.plain_url_email_change_confirm, args=('invalidkey',))
        response = self.client.get(url_email_change_confirm)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user(self):
        email = self.emails.next()
        token, id = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], email)

    def test_retrieve_user_fail_permission(self):
        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partially_update_user(self):
        token, id = self._create_activated_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'firstName': 'Falk',
            'lastName': 'Benke',
            'profile': {'country': 'DE'}
        }
        response = self.client.patch(self.url_profile, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_user(self):
        email = self.emails.next()
        token, id = self._create_activated_user(email=email, password=self.password)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials(HTTP_AUTHORIZATION=None)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset(self):
        email = self.emails.next()
        token, id = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        no_emails = len(mailbox.outbox)

        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get confirmation key and send activate get request
        uid, token = self._generate_password_reset_confirmation_key(id)
        url_confirm = reverse(self.plain_url_password_reset_confirm, args=(uid, token))

        # check if mail contains correct link
        self.assertTrue(settings.MAIL_PASSWORD_RESET_URL.format(uid, token) in mailbox.outbox[no_emails].body)

        # send a get request to check if the generated token/uid combination is valid
        response = self.client.get(url_confirm)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change password
        response = self.client.post(url_confirm, {'password1': self.new_password, 'password2': self.new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # fails to signin with old credentials
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # signin with new credentials
        response = self.client.post(self.url_signin, {'email': email, 'password': self.new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_password_reset_fail_email_unknown(self):
        email = self.emails.next()
        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_UNKNOWN)

    def test_password_reset_fail_user_incative(self):
        email = self.emails.next()
        self._create_user(email)
        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_ACCOUNT_DISABLED)

    def test_password_change(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'oldPassword': self.password,
            'password1': self.new_password,
            'password2': self.new_password
        }

        response = self.client.post(self.url_password_change, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)

        response = self.client.post(self.url_signin, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token')

        response = self.client.post(self.url_signin, {'email': email, 'password': self.new_password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token')

    def test_aws_upload_invalid_params(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_aws_upload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_aws_upload_profile_incomplete(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_PROFILE_INCOMPLETE)

    def test_aws_upload_invalid_document_status(self):
        email = self.emails.next()
        token, id = self._create_user_with_profile(email=email)
        user = get_user_model().objects.get(id=id)
        user.profile.passport_state = Profile.UPLOADED
        user.profile.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENT_ALREADY_UPLOADED)

    def test_aws_upload_incomplete_profile(self):
        email = self.emails.next()
        token, _ = self._create_user_with_profile(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_verification_status(self):
        email = self.emails.next()
        token, id = self._create_user_with_profile(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[Profile.IDENTIFICATION], Profile.EMPTY)
        self.assertEqual(response.data[Profile.PROOF_OF_RESIDENCE], Profile.EMPTY)
        self.assertEqual(response.data['information_complete'], True)

        user = get_user_model().objects.get(id=id)
        user.profile.passport_state = Profile.UPLOADED
        user.profile.proof_of_residence_state = Profile.VERIFIED
        user.profile.save()
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[Profile.IDENTIFICATION], Profile.UPLOADED)
        self.assertEqual(response.data[Profile.PROOF_OF_RESIDENCE], Profile.VERIFIED)
        self.assertEqual(response.data['information_complete'], True)

        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['PAS'], 'EMP')
        self.assertEqual(response.data['POR'], 'EMP')
        self.assertEqual(response.data['information_complete'], False)

    def test_upload_confirmation_incomplete_profile(self):

        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {'document': Profile.IDENTIFICATION}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_PROFILE_INCOMPLETE)

    def test_upload_confirmation_invalid_document_status(self):
        email = self.emails.next()
        token, id = self._create_user_with_profile(email=email)
        user = get_user_model().objects.get(id=id)
        user.profile.passport_state = Profile.UPLOADED
        user.profile.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {'document': Profile.IDENTIFICATION}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENT_ALREADY_UPLOADED)

    def test_upload_confirmation(self):
        no_emails = len(mailbox.outbox)

        email = self.emails.next()
        token, _ = self._create_user_with_profile(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {'document': Profile.IDENTIFICATION}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mailbox.outbox), no_emails + 1)
