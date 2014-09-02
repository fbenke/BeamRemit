from django.core.urlresolvers import reverse
from django.core import mail as mailbox
from django.utils import timezone

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
    plain_url_activate = 'accounts:activate'

    password = 'Django123'

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 1000)])

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
        self._create_user(email, password)
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        return response.data['token'], response.data['id']

    def test_signup(self):
        # test signup
        email = self.emails.next()
        response = self._create_user(email=email)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'success')

        # assert that mail was sent
        self.assertEqual(len(mailbox.outbox), 1)

        # get activation key and send activate get request
        activation_key = get_user_model().objects.get(email__iexact=email).userena_signup.activation_key
        url_activate = reverse(self.plain_url_activate, args=(activation_key,))
        response = self.client.get(url_activate)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['activation_key'] is not None)
        self.assertEqual(response.data['detail'], 'Activation Key has expired.')

    def test_signin(self):
        email = self.emails.next()
        self._create_activated_user(email=email)
        response = self.client.post(self.url_signin, {'email': email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

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
        email = self.emails.next()
        token, _ = self._create_activated_user(email=email)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_singout)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')


# activation retry, validation errors login, signup
