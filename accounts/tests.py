from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from userena.models import UserenaSignup


class CreateUserTests(APITestCase):

    url_signup = reverse('accounts:signup')
    url_login = reverse('user:login')
    url_logout = reverse('user:logout')

    password = 'Django123'

    mails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 1000)])

    def setUp(self):
        UserenaSignup.objects.check_permissions()

    def _createUser(self, mail=None, password=None):
        if mail is None:
            mail = self.mails.next()
        if password is None:
            password = self.password
        data = {
            'email': mail,
            'password1': password,
            'password2': password,

        }
        response = self.client.post(self.url_signup, data)
        return response

    def test_signup(self):
        response = self._createUser()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'success')



    # def test_login(self):
    #     mail = self.mails.next()
    #     self.createUser(mail=mail, password=self.password)
    #     response = self.client.post(self.url_login, {'email': mail, 'password': 'Django123'})
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertTrue(response.data['token'] is not None)
    #     self.assertTrue(response.data['id'] is not None)

    # def test_login_failure(self):
    #     mail = self.mails.next()
    #     self.createUser(mail=mail, password='Django123')
    #     response = self.client.post(self.url_login, {'email': mail, 'password': 'Django321'})
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)