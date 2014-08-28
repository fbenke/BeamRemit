from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CreateUserTests(APITestCase):

    url = reverse('user:create')
    data = {
        'email': 'falk@mail.com',
        'first_name': 'Falk',
        'last_name': 'Benke',
        'password': 'Django1'
    }

    def test_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_validation_empty(self):
        'empty post'
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_incomplete(self):
        'incomplete post'
        self.data.pop('last_name', 0)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['last_name'][0], 'This field is required.')

    def test_validation_duplicate_mail(self):
        'duplicate mail'
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'Beam user with this Email already exists.')

    def test_validation_password_format(self):
        'violating password format'
        self.data['password'] = 'Django'
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must be at least 6 characters long, contain at leastone upper case letter, one lower case letter, and one numeric digit.')
