from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CreateUserTests(APITestCase):
    url_signup = reverse('user:create')
    url_login = reverse('user:login')
    url_logout = reverse('user:logout')

    mails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 1000)])

    def createUser(self, mail=None, password='Django123', first_name='Test', last_name='Hans'):
        if mail is None:
            mail = self.mails.next()
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': mail,
            'password': password,
        }
        response = self.client.post(self.url_signup, data)
        return response.data['token'], response.data['id']

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
        self.createUser(mail='falk@mail.com', password='Django123')
        response = self.client.post(self.url_login, {'email': 'falk@mail.com', 'password': 'Django321'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(self.url_login, {'email': 'falk@mail.com', 'password': 'Django123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'] is not None)
        self.assertTrue(response.data['id'] is not None)

    def test_logout(self):
        token, _ = self.createUser()
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
            'email': self.mails.next(),
            'password': 'Django123'
        }
        response = self.client.post(self.url_signup, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['last_name'][0], 'This field is required.')

    def test_validation_duplicate_mail(self):
        'duplicate mail'
        self.createUser(mail='falk2@mail.com')
        data = {
            'first_name': 'Falk',
            'last_name': 'Benke',
            'email': 'falk2@mail.com',
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

    def test_retrieve_user(self):
        token, id = self.createUser()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        url_retrieve = reverse('user:change', args=(id,))
        response = self.client.get(url_retrieve)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_user_fail(self):
        token, id = self.createUser()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        url_retrieve = reverse('user:change', args=(id + 1,))
        response = self.client.get(url_retrieve)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_user_fail_permission(self):
        url_retrieve = reverse('user:change', args=(0,))
        response = self.client.get(url_retrieve)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
