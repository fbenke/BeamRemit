from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CreateUserTests(APITestCase):
    url_signup = reverse('user:create')
    url_login = reverse('user:login')
    url_logout = reverse('user:logout')

    def createUser(self, mail, password='Django123', first_name='Test', last_name='Hans'):
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': mail,
            'password': password,
        }
        response = self.client.post(self.url_signup, data)
        return response.data['token']

    def test_signup(self):
        data = {
            'first_name': 'Falk',
            'last_name': 'Benke',
            'email': 'test1@mail.com',
            'password': 'Django123'
        }

        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_login(self):
        self.createUser(mail='test2@mail.com')
        response = self.client.post(self.url_login, {'email': 'test2@mail.com', 'password': 'Django123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_logout(self):
        token = self.createUser(mail='test3@mail.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_logout)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_validation_empty(self):
        'empty post'
        response = self.client.post(self.url_signup, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_incomplete(self):
        'incomplete post'
        data = {
            'first_name': 'Falk',
            'email': 'test4@mail.com',
            'password': 'Django123'
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['last_name'][0], 'This field is required.')

    def test_validation_duplicate_mail(self):
        'duplicate mail'
        self.createUser(mail='test4@mail.com')
        data = {
            'first_name': 'Falk',
            'last_name': 'Benke',
            'email': 'test4@mail.com',
            'password': 'Django123'
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'Beam user with this Email already exists.')

    def test_validation_password_format(self):
        'violating password format'
        data = {
            'first_name': 'Falk',
            'last_name': 'Benke',
            'email': 'test5@mail.com',
            'password': 'Django'
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must be at least 6 characters long, contain at leastone upper case letter, one lower case letter, and one numeric digit.')
