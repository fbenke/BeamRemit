from django.contrib.auth.tokens import default_token_generator as token_generator
from django.core.urlresolvers import reverse
from django.core import mail as mailbox
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from rest_framework import status
from rest_framework.test import APITestCase

from userena.models import UserenaSignup
from userena.utils import get_user_model

from datetime import timedelta

from django.conf import settings


class CreateUserTests(APITestCase):

    url_signup = reverse('accounts:signup')
    url_signin = reverse('accounts:signin')
    url_singout = reverse('accounts:signout')
    url_email_change = reverse('accounts:email_change')
    url_password_reset = reverse('accounts:password_reset')
    url_password_change = reverse('accounts:password_change')
    url_profile = reverse('accounts:profile')
    plain_url_activate = 'accounts:activate'
    plain_url_activate_retry = 'accounts:activate_retry'
    plain_url_email_change_confirm = 'accounts:email_confirm'
    plain_url_password_reset_confirm = 'accounts:password_reset_confirm'

    password = 'Django123'
    new_password = 'Django321'

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 100)])

    def setUp(self):
        UserenaSignup.objects.check_permissions()

    def _create_user(self, email=None, password=None):
        if email is None:
            email = self.emails.next()
        if password is None:
            password = self.password
        data = {
            'email': email,
            'password1': password,
            'password2': password,

        }
        response = self.client.post(self.url_signup, data)
        return response

    def _create_activated_user(self, email=None, password=None):
        if email is None:
            email = self.emails.next()
        self._create_user(email, password)
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        return response.data['token'], response.data['id']

    def _generate_password_reset_confirmation_key(self, id):
        user = get_user_model().objects.get(id=id)
        return urlsafe_base64_encode(force_bytes(user.pk)), token_generator.make_token(user)

    def test_signup(self):

        no_emails = len(mailbox.outbox)

        email = self.emails.next()
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Success')

        # assert that mail was sent
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get activation key and send activate get request
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))

        # check if mail contains correct link
        # TODO: replace `url_activate` with the real link later
        self.assertTrue(url_activate in mailbox.outbox[0].body)
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
        self.assertEqual(response.data['non_field_errors'][0], "The two password fields didn't match.")

    def test_signup_validation_unconfirmed_mail(self):
        'duplicate mail'
        email = self.emails.next()
        self._create_user(email=email)
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'This email is already in use but not confirmed. Please check your email for verification steps.')

    def test_signup_validation_duplicate_mail(self):
        'duplicate mail'
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'This email is already in use.')

    def test_activation_invalid_key(self):
        url_activate = reverse(self.plain_url_activate, args=('invalidkey',))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid Key')

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
        self.assertEqual(response.data['detail'], 'Activation Key has expired')

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
        self.assertEqual(response.data['detail'], 'Invalid Key')

    def test_activation_retry_valid_key(self):
        email = self.emails.next()
        self._create_user(email)
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate_retry = reverse(self.plain_url_activate_retry, args=(activation_key,))
        response = self.client.get(url_activate_retry)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Key is not expired')

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
        self.assertEqual(response.data['non_field_errors'][0], 'Unable to login with provided credentials.')

    def test_singin_without_activation(self):
        email = self.emails.next()
        self._create_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], 'User account is disabled.')

    def test_signout(self):
        token, _ = self._create_activated_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_singout)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Success')

    def test_email_change(self):
        old_email = self.emails.next()
        token, _ = self._create_activated_user(email=old_email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        no_emails = len(mailbox.outbox)
        new_mail = self.emails.next()
        response = self.client.post(self.url_email_change, {'email': new_mail})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Success')

        # assert that two mails were sent
        self.assertEqual(len(mailbox.outbox), no_emails + 2)

        # check if corresponding database fields exist
        user = get_user_model().objects.get(email__iexact=old_email)
        self.assertEqual(user.userena_signup.email_unconfirmed, new_mail)

        confirmation_key = user.userena_signup.email_confirmation_key

        url_email_change_confirm = reverse(self.plain_url_email_change_confirm, args=(confirmation_key,))
        response = self.client.get(url_email_change_confirm)
        self.assertEqual(response.data['detail'], 'Success')
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
        self.assertEqual(response.data['detail'], 'Invalid Parameters')

    def test_email_change_failure_same_mail(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_email_change, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'You are already known under this email.')

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
        self.assertEqual(response.data['detail'], 'This email is already in use. Please supply a different email.')

    def test_email_change_confirm_failure(self):
        url_email_change_confirm = reverse(self.plain_url_email_change_confirm, args=('invalidkey',))
        response = self.client.get(url_email_change_confirm)
        self.assertEqual(response.data['detail'], 'Invalid Parameters')
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
            'first_name': 'Falk',
            'last_name': 'Benke',
            'profile': {'country': 'DE'}
        }
        response = self.client.patch(self.url_profile, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Falk')
        self.assertEqual(response.data['last_name'], 'Benke')
        self.assertEqual(response.data['profile']['country'], 'DE')

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
        url = reverse('accounts:password_reset')

        response = self.client.post(url, {'email': email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Success')

        self.assertEqual(len(mailbox.outbox), no_emails + 1)

        # get confirmation key and send activate get request
        uid, token = self._generate_password_reset_confirmation_key(id)
        url_confirm = reverse(self.plain_url_password_reset_confirm, args=(uid, token))

        # check if mail contains correct link
        # TODO: replace `url_activate` with the real link later
        self.assertTrue(url_confirm in mailbox.outbox[no_emails].body)

        # send a get request to check if the generated token/uid combination is valid
        response = self.client.get(url_confirm)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Success')

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

    def test_password_change(self):
        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'old_password': self.password,
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
