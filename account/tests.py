from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.sites.models import Site

from django.core.urlresolvers import reverse
from django.core import mail as mailbox
from django.test import TestCase
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_framework import status
from rest_framework.test import APITestCase

from userena.models import UserenaSignup

from datetime import timedelta
import datetime

from mock import patch
# from unittest import skip

from account import constants
from account.models import DocumentStatusChange, BeamProfile as Profile

from beam.tests import TestUtils


class AccountTests(APITestCase, TestUtils):

    url_signup = reverse('account:signup')
    url_profile = reverse('account:profile')
    url_signin = reverse('account:signin')
    url_singout = reverse('account:signout')
    url_email_change = reverse('account:email_change')
    url_password_reset = reverse('account:password_reset')
    url_password_change = reverse('account:password_change')
    url_activate_resend = reverse('account:activate_resend')
    url_aws_upload = reverse('account:aws')
    url_upload_complete = reverse('account:upload_complete')
    url_verification_status = reverse('account:verification_status')
    url_account_limits = reverse('account:limit')

    plain_url_activate = 'account:activate'
    plain_url_activate_retry = 'account:activate_retry'
    plain_url_email_change_confirm = 'account:email_confirm'
    plain_url_password_reset_confirm = 'account:password_reset_confirm'

    @classmethod
    def setUpClass(cls):
        UserenaSignup.objects.check_permissions()

    def _generate_password_reset_confirmation_key(self, id):
        user = User.objects.get(id=id)
        return urlsafe_base64_encode(force_bytes(user.pk)), token_generator.make_token(user)

    def tearDown(self):
        self.client.logout()


class SignupTests(AccountTests):

    def test_signup(self):
        'successful signup and activation'

        no_emails = len(mailbox.outbox)

        email = self.emails.next()

        data = {
            'email': email,
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': True,
        }
        response = self.client.post(self.url_signup, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert that mail was sent
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get activation key and send activate get request
        activation_key = User.objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))

        # check if mail contains correct link
        self.assertTrue(settings.MAIL_ACTIVATION_URL.format(activation_key) in mailbox.outbox[0].body)
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_signup_site(self):
        email = self.emails.next()
        data = {
            'email': email,
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': True,
        }
        self.client.post(self.url_signup, data, HTTP_REFERER='http://dev.bitcoinagainstebola.org')
        self.assertEqual(User.objects.get(email=email).profile.signup_site_id, 1)
        email = self.emails.next()
        data = {
            'email': email,
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': True,
        }
        self.client.post(self.url_signup, data, HTTP_REFERER='http://dev.beamremit.com')
        self.assertEqual(User.objects.get(email=email).profile.signup_site_id, 0)

    def test_signup_validation_empty(self):
        'empty post'
        response = self.client.post(self.url_signup, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_validation_incomplete(self):
        'incomplete post'
        data = {
            'email': self.emails.next(),
            'password1': self.default_password
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password2'][0], 'This field is required.')
        self.assertEqual(response.data['accepted_privacy_policy'][0], 'This field is required.')

    def test_signup_validation_password_mismatch(self):
        'password mismatch'
        data = {
            'email': self.emails.next(),
            'password1': self.default_password,
            'password2': self.default_password[1:],
            'acceptedPrivacyPolicy': True
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.PASSWORD_MISMATCH)

    def test_signup_validation_unconfirmed_mail(self):
        'unconfiremd email'
        email = self.emails.next()
        self._create_inactive_user(email=email)
        data = {
            'email': email,
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': True,
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], constants.EMAIL_IN_USE_UNCONFIRMED)

    def test_signup_validation_duplicate_mail(self):
        'duplicate mail'
        email = self.emails.next()
        self._create_activated_user(email=email)
        data = {
            'email': email,
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': True,
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], constants.EMAIL_IN_USE)

    def test_signup_validation_privacy_policy(self):
        'privacy policy not accepted'
        data = {
            'email': self.emails.next(),
            'password1': self.default_password,
            'password2': self.default_password,
            'acceptedPrivacyPolicy': False
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['accepted_privacy_policy'][0], constants.PRIVACY_POLICY_NOT_ACCEPTED)


class ActivationTests(AccountTests):

    def test_activation_invalid_key(self):
        url_activate = reverse(self.plain_url_activate, args=('invalidkey',))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_INVALID)

    def test_activation_expired_key(self):
        email = self.emails.next()
        user = self._create_inactive_user(email=email)

        # manipulate db so that activation key is expired
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
        activation_key = User.objects.get(email__iexact=email).userena_signup.activation_key
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
        user = self._create_inactive_user()
        activation_key = user.userena_signup.activation_key
        url_activate_retry = reverse(self.plain_url_activate_retry, args=(activation_key,))
        response = self.client.get(url_activate_retry)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_NOT_EXPIRED)

    def test_activation_resend(self):
        email = self.emails.next()
        self._create_inactive_user(email=email)

        no_emails = len(mailbox.outbox)
        response = self.client.post(self.url_activate_resend, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        activation_key = User.objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_activation_resend_unknown_email(self):
        email = self.emails.next()
        response = self.client.post(self.url_activate_resend, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_UNKNOWN)

    def test_activation_resend_account_already_activated(self):
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self.client.post(self.url_activate_resend, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_ACCOUNT_ALREADY_ACTIVATED)

    def test_activation_overwritten_key(self):
        email = self.emails.next()
        user = self._create_inactive_user(email=email)
        response = self.client.post(self.url_activate_resend, {'email': email})
        activation_key = user.userena_signup.activation_key
        response = self.client.post(self.url_activate_resend, {'email': email})
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ACTIVATION_KEY_INVALID)


class SigninTests(AccountTests):

    def test_signin(self):
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password})
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
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password[1:]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.SIGNIN_WRONG_CREDENTIALS)

    def test_singin_without_activation(self):
        email = self.emails.next()
        self._create_inactive_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.USER_ACCOUNT_DISABLED)

    def test_signin_with_admin_account(self):
        email = self.emails.next()
        self._create_admin_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.ADMIN_ACCOUNT)

    def test_signout(self):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_singout)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EmailChangeTests(AccountTests):

    def test_email_change(self):
        old_email = self.emails.next()
        user = self._create_activated_user(email=old_email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        no_emails = len(mailbox.outbox)
        new_mail = self.emails.next()
        response = self.client.post(self.url_email_change, {'email': new_mail})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that two mails were sent, to old and new account
        self.assertEqual(len(mailbox.outbox), no_emails + 2)
        mailbox.outbox[0].from_email in (old_email, new_mail)
        mailbox.outbox[1].from_email in (old_email, new_mail)

        # check if corresponding database fields exist
        user = User.objects.get(email__iexact=old_email)
        self.assertEqual(user.userena_signup.email_unconfirmed, new_mail)

        confirmation_key = user.userena_signup.email_confirmation_key

        url_email_change_confirm = reverse(self.plain_url_email_change_confirm, args=(confirmation_key,))
        response = self.client.get(url_email_change_confirm)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # verify that new email address is active and old no longer in use
        self.assertIsNotNone(User.objects.get(email__iexact=new_mail))
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email__iexact=old_email)

    def test_email_change_failure_empty(self):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_email_change, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_email_change_failure_same_mail(self):
        email = self.emails.next()
        user = self._create_activated_user(email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_email_change, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.EMAIL_NOT_CHANGED)

    def test_email_change_failure_existing_mail(self):
        # create a user with email
        email = self.emails.next()
        self._create_activated_user(email)
        # create another user
        user = self._create_activated_user()
        token = self._create_token(user)

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


class PasswordResetTests(AccountTests):

    def test_password_reset(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        no_emails = len(mailbox.outbox)

        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get confirmation key and send activate get request
        uid, token = self._generate_password_reset_confirmation_key(user.id)
        url_confirm = reverse(self.plain_url_password_reset_confirm, args=(uid, token))

        # check if mail contains correct link
        self.assertTrue(settings.MAIL_PASSWORD_RESET_URL.format(uid, token) in mailbox.outbox[no_emails].body)
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # send a get request to check if the generated token/uid combination is valid
        response = self.client.get(url_confirm)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change password
        response = self.client.post(url_confirm, {
            'password1': self.default_new_password,
            'password2': self.default_new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # fails to signin with old credentials
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # signin with new credentials
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_new_password})
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
        self._create_inactive_user(email)
        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_ACCOUNT_DISABLED)

    def test_password_reset_invalid_rparameter(self):
        url_confirm = reverse(self.plain_url_password_reset_confirm, args=('123', '345'))
        response = self.client.get(url_confirm)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_password_reset_invalid_changes(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_password_reset, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uid, token = self._generate_password_reset_confirmation_key(user.id)
        url_confirm = reverse(self.plain_url_password_reset_confirm, args=(uid, token))

        #  password mismatch
        response = self.client.post(url_confirm, {
            'password1': self.default_new_password,
            'password2': self.default_new_password[1:]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], constants.PASSWORD_MISMATCH)

        # password invalid format
        response = self.client.post(url_confirm, {
            'password1': self.default_invalid_password,
            'password2': self.default_invalid_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password1'][0], constants.PASSWORD_FORMAT)


class PasswordChangeTests(AccountTests):

    def test_permissions(self):
        response = self.client.post(self.url_password_change)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'oldPassword': self.default_password,
            'password1': self.default_new_password,
            'password2': self.default_new_password
        }

        response = self.client.post(self.url_password_change, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        new_token = response.data['token']

        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + new_token)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change_fail(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'oldPassword': self.default_new_password,
            'password1': self.default_new_password,
            'password2': self.default_new_password
        }
        response = self.client.post(self.url_password_change, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['old_password'][0], constants.PASSWORD_OLD_INCORRECT)


class ProfileTests(AccountTests):

    def test_permissions(self):
        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.put(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], email)

    def test_retrieve_user_fail_permission(self):
        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fill_out_profile(self):
        email = self.emails.next()
        user = self._create_activated_user(email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.patch(self.url_profile, self.default_profile)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email__iexact=email)
        self.assertEqual(user.first_name, 'Falk')
        self.assertEqual(user.last_name, 'Benke')
        self.assertEqual(user.profile.country, 'DE')
        self.assertEqual(user.profile.city, 'Berlin')
        self.assertEqual(user.profile.date_of_birth, datetime.date(1985, 10, 4))
        self.assertEqual(user.profile.street, 'Platz der Vereinten Nationen 23')
        self.assertEqual(user.profile.post_code, '10249')
        self.assertEqual(len(DocumentStatusChange.objects.filter(profile=user.profile)), 0)
        response = self.client.patch(self.url_profile, self.default_profile)
        self.assertEqual(len(DocumentStatusChange.objects.filter(profile=user.profile)), 0)

    def test_partially_update_user(self):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'first_name': 'Falk',
            'last_name': 'Benke',
            'profile': {'country': 'DE'}
        }
        response = self.client.patch(self.url_profile, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url_profile)
        self.assertEqual(response.data['first_name'], 'Falk')
        self.assertEqual(response.data['last_name'], 'Benke')
        self.assertEqual(response.data['profile']['country'], 'DE')

    def test_delete_user(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email, password=self.default_password)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.delete(self.url_profile)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials(HTTP_AUTHORIZATION=None)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.default_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_user_reset_documents(self):
        no_document_state_changes = DocumentStatusChange.objects.all().count()
        email = self.emails.next()
        user = self._create_fully_verified_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.patch(self.url_profile, {'first_name': 'NewF', 'profile': {}})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(id=user.id)

        self.assertEqual(user.profile.identification_state, Profile.EMPTY)
        self.assertEqual(user.profile.proof_of_residence_state, Profile.VERIFIED)

        self.client.patch(self.url_profile, {'profile': {'country': 'GH'}})
        user = User.objects.get(id=user.id)
        self.assertEqual(user.profile.proof_of_residence_state, Profile.EMPTY)

        self.assertEqual(DocumentStatusChange.objects.all().count(), no_document_state_changes + 2)
        changes = DocumentStatusChange.objects.filter(profile=user.profile)
        for c in changes:
            self.assertEqual(c.changed_by, 'user')
            self.assertEqual(c.changed_to, Profile.EMPTY)
            self.assertEqual(c.reason, '')


class AWSTests(AccountTests):

    def test_permissions(self):
        response = self.client.get(self.url_aws_upload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('account.views.generate_aws_upload')
    def test_aws_upload(self, mock_upload):
        mock_upload.return_value = {'key': 'value'}
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['key'], 'value')
        mock_upload.assert_called_with('{}_{}'.format(Profile.DOCUMENT_TYPES[0], user.id), 'image/png')

    def test_aws_upload_invalid_params(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_aws_upload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

        response = self.client.get(self.url_aws_upload + '?documenttype=INVALID&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_aws_upload_profile_incomplete(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_PROFILE_INCOMPLETE)

    def test_aws_upload_invalid_document_status(self):
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        user.profile.identification_state = Profile.UPLOADED
        user.profile.save()
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(
            self.url_aws_upload + '?documenttype=' + Profile.DOCUMENT_TYPES[0] +
            '&contenttype=image/png')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENT_ALREADY_UPLOADED)


class UploadCompleteTests(AccountTests):

    def test_permissions(self):
        response = self.client.post(self.url_upload_complete)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_confirmation_incomplete_profile(self):
        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {'document': Profile.IDENTIFICATION}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.USER_PROFILE_INCOMPLETE)

    def test_upload_confirmation_invalid_document_status(self):
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        user.profile.identification_state = Profile.UPLOADED
        user.profile.proof_of_residence_state = Profile.VERIFIED
        user.profile.save()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.post(self.url_upload_complete, self.default_id_document)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENT_ALREADY_UPLOADED)

        data = {'document': Profile.PROOF_OF_RESIDENCE}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENT_ALREADY_UPLOADED)

    def test_upload_invalid_params(self):
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {'document': Profile.IDENTIFICATION}
        response = self.client.post(self.url_upload_complete, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.INVALID_PARAMETERS)

    def test_upload_confirmation(self):
        self._create_admin_user()
        no_emails = len(mailbox.outbox)
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.post(self.url_upload_complete, self.default_id_document)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.get(id=user.id).profile.identification_state, Profile.UPLOADED)

        response = self.client.post(self.url_upload_complete, {'document': Profile.PROOF_OF_RESIDENCE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.get(id=user.id).profile.proof_of_residence_state, Profile.UPLOADED)

        self.assertEqual(len(mailbox.outbox), no_emails + 2)


class VerificationStatusTests(AccountTests):

    def test_permissions(self):
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verification_status(self):
        email = self.emails.next()
        user = self._create_user_with_profile(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[Profile.IDENTIFICATION], Profile.EMPTY)
        self.assertEqual(response.data[Profile.PROOF_OF_RESIDENCE], Profile.EMPTY)
        self.assertEqual(response.data['information_complete'], True)

        user.profile.identification_state = Profile.UPLOADED
        user.profile.proof_of_residence_state = Profile.VERIFIED
        user.profile.save()
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[Profile.IDENTIFICATION], Profile.UPLOADED)
        self.assertEqual(response.data[Profile.PROOF_OF_RESIDENCE], Profile.VERIFIED)
        self.assertEqual(response.data['information_complete'], True)

        email = self.emails.next()
        user = self._create_activated_user(email=email)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(self.url_verification_status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['PAS'], 'EMP')
        self.assertEqual(response.data['POR'], 'EMP')
        self.assertEqual(response.data['information_complete'], False)


class AccountLimitTests(AccountTests):

    def setUp(self):
        self.exchange_rate = self._create_default_exchange_rate()
        self.limit_bae = self._create_default_limit_bae()
        self.limit_beam = self._create_default_limit_beam()

    def test_permissions(self):
        response = self.client.get(self.url_account_limits)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_account_limits_activated_user(self):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 40)
        self.assertEqual(response.data['currency'], 'GBP')
        self.assertEqual(response.data['today'], 0)
        self.assertTrue(response.data['can_extend'])

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 50)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['today'], 0)
        self.assertTrue(response.data['can_extend'])

    def test_account_limits_fully_verified_user(self):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 500)
        self.assertEqual(response.data['currency'], 'GBP')
        self.assertEqual(response.data['today'], 0)
        self.assertFalse(response.data['can_extend'])

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 600)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['today'], 0)
        self.assertFalse(response.data['can_extend'])

    def test_account_spending_count(self):

        user = self._create_fully_verified_user()
        token = self._create_token(user)

        self._create_transaction(
            sender=user,
            exchange_rate=self.exchange_rate,
            pricing=self._create_default_pricing_beam(),
            sent_amount=200,
            sent_currency='GBP',
            received_amount=1028.2,
            receiving_country='GH'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 500)
        self.assertEqual(response.data['currency'], 'GBP')
        self.assertEqual(response.data['today'], 200)
        self.assertFalse(response.data['can_extend'])

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 600)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['today'], 320)
        self.assertFalse(response.data['can_extend'])

        self._create_transaction(
            sender=user,
            exchange_rate=self.exchange_rate,
            pricing=self._create_default_pricing_bae(),
            sent_amount=12,
            sent_currency='USD',
            received_amount=39.75,
            receiving_country='SL'
        )

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 500)
        self.assertEqual(response.data['currency'], 'GBP')
        self.assertEqual(response.data['today'], 207.5)
        self.assertFalse(response.data['can_extend'])

        response = self.client.get(self.url_account_limits, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 600)
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['today'], 332)
        self.assertFalse(response.data['can_extend'])


class AdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user(self.emails.next())
        self.client.login(username=admin.username, password=self.default_password)

    def test_view_account_sites(self):

        response = self.client.get(reverse('admin:account_beamprofile_changelist'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('admin:account_documentstatuschange_changelist'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = self._create_user_with_profile()
        response = self.client.get(reverse('admin:account_beamprofile_change', args=(user.profile.id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_documents(self):

        user = self._create_user_with_uploaded_documents()
        no_document_state_changes = DocumentStatusChange.objects.all().count()
        no_emails = len(mailbox.outbox)

        data = {
            'identification_state': Profile.VERIFIED,
            'identification_number': self.default_identification_number,
            'identification_issue_date': self.default_identification_issue_date,
            'identification_expiry_date': self.default_identification_expiry_date,
            'send_identification_mail': 'on',
            'identification_reason': 'INI',
            'proof_of_residence_state': Profile.VERIFIED,
            'send_proof_of_residence_mail': 'on',
            'proof_of_residence_reason': 'EXP',
            'document_status_change-__prefix__-profile': user.profile.id,
            'document_status_change-TOTAL_FORMS': '0',
            'document_status_change-INITIAL_FORMS': '0',
            'document_status_change-MAX_NUM_FORMS': '10',
            '_continue': 'Save and continue editing',
            'document_status_change-__prefix__-id': ''
        }

        response = self.client.post(reverse(
            'admin:account_beamprofile_change',
            args=(user.profile.id,)), data
        )

        user = User.objects.get(id=user.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(user.profile.identification_state, Profile.VERIFIED)
        self.assertEqual(user.profile.proof_of_residence_state, Profile.VERIFIED)
        self.assertEqual(len(mailbox.outbox), no_emails + 2)
        self.assertEqual(DocumentStatusChange.objects.all().count(), no_document_state_changes + 2)

        changes = DocumentStatusChange.objects.filter(profile=user.profile)
        for c in changes:
            self.assertEqual(c.changed_by, self.default_username)
            self.assertEqual(c.changed_to, Profile.VERIFIED)
            self.assertEqual(c.reason, '')

    def test_change_documents_without_notification(self):

        user = self._create_user_with_uploaded_documents()
        no_document_state_changes = DocumentStatusChange.objects.all().count()
        no_emails = len(mailbox.outbox)

        data = {
            'identification_state': Profile.VERIFIED,
            'identification_number': self.default_identification_number,
            'identification_issue_date': self.default_identification_issue_date,
            'identification_expiry_date': self.default_identification_expiry_date,
            'identification_reason': 'INI',
            'proof_of_residence_state': Profile.VERIFIED,
            'proof_of_residence_reason': 'EXP',
            'document_status_change-__prefix__-profile': user.profile.id,
            'document_status_change-TOTAL_FORMS': '0',
            'document_status_change-INITIAL_FORMS': '0',
            'document_status_change-MAX_NUM_FORMS': '10',
            '_continue': 'Save and continue editing',
            'document_status_change-__prefix__-id': ''
        }

        response = self.client.post(reverse(
            'admin:account_beamprofile_change',
            args=(user.profile.id,)), data
        )

        user = User.objects.get(id=user.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(user.profile.identification_state, Profile.VERIFIED)
        self.assertEqual(user.profile.proof_of_residence_state, Profile.VERIFIED)
        self.assertEqual(len(mailbox.outbox), no_emails)
        self.assertEqual(DocumentStatusChange.objects.all().count(), no_document_state_changes + 2)

        changes = DocumentStatusChange.objects.filter(profile=user.profile)
        for c in changes:
            self.assertEqual(c.changed_by, self.default_username)
            self.assertEqual(c.changed_to, Profile.VERIFIED)
            self.assertEqual(c.reason, '')

    def test_decline_documents(self):

        user = self._create_user_with_uploaded_documents()
        no_document_state_changes = DocumentStatusChange.objects.all().count()
        no_emails = len(mailbox.outbox)

        data = {
            'identification_state': Profile.FAILED,
            'identification_number': self.default_identification_number,
            'identification_issue_date': self.default_identification_issue_date,
            'identification_expiry_date': self.default_identification_expiry_date,
            'send_identification_mail': 'on',
            'identification_reason': DocumentStatusChange.LOW_QUALITY,
            'proof_of_residence_state': Profile.FAILED,
            'send_proof_of_residence_mail': 'on',
            'proof_of_residence_reason': DocumentStatusChange.LOW_QUALITY,
            'document_status_change-__prefix__-profile': user.profile.id,
            'document_status_change-TOTAL_FORMS': '0',
            'document_status_change-INITIAL_FORMS': '0',
            'document_status_change-MAX_NUM_FORMS': '10',
            '_continue': 'Save and continue editing',
            'document_status_change-__prefix__-id': ''
        }

        response = self.client.post(reverse(
            'admin:account_beamprofile_change',
            args=(user.profile.id,)), data
        )

        user = User.objects.get(id=user.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(user.profile.identification_state, Profile.FAILED)
        self.assertEqual(user.profile.proof_of_residence_state, Profile.FAILED)
        self.assertEqual(len(mailbox.outbox), no_emails + 2)
        self.assertEqual(DocumentStatusChange.objects.all().count(), no_document_state_changes + 2)

        changes = DocumentStatusChange.objects.filter(profile=user.profile)
        for c in changes:
            self.assertEqual(c.changed_by, self.default_username)
            self.assertEqual(c.changed_to, Profile.FAILED)
            self.assertEqual(c.reason, DocumentStatusChange.LOW_QUALITY)


class ProfileModelTests(TestCase, TestUtils):

    def test_transaction_volume(self):
        user = self._create_fully_verified_user()
        pricing_beam = self._create_default_pricing_beam()
        pricing_bae = self._create_default_pricing_bae()
        exchange_rate = self._create_default_exchange_rate()
        site_beam = Site.objects.get(id=0)
        site_bae = Site.objects.get(id=1)

        self.assertEqual(user.profile.todays_transaction_volume(site_beam), 0)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae), 0)
        self.assertEqual(user.profile.todays_transaction_volume(site_beam, 1.23), 1.23)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae, 9.81), 9.81)

        self._create_transaction(
            sender=user,
            pricing=pricing_beam,
            exchange_rate=exchange_rate,
            sent_amount=93,
            sent_currency='GBP',
            received_amount=478.2,
            receiving_country='GH'
        )

        self.assertEqual(user.profile.todays_transaction_volume(site_beam), 93)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae), 148.8)
        self.assertEqual(user.profile.todays_transaction_volume(site_beam, 10), 103)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae, 10), 158.8)

        self._create_transaction(
            sender=user,
            pricing=pricing_bae,
            sent_amount=18,
            exchange_rate=exchange_rate,
            sent_currency='USD',
            received_amount=77050,
            receiving_country='SL'
        )

        self.assertEqual(user.profile.todays_transaction_volume(site_beam), 104.25)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae), 166.8)
        self.assertEqual(user.profile.todays_transaction_volume(site_beam, 15), 119.25)
        self.assertEqual(user.profile.todays_transaction_volume(site_bae, 15), 181.8)
