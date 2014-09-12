from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from userena.models import UserenaSignup
from userena.utils import get_user_model


class BeamAPITestCase(APITestCase):

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 100)])
    password = 'Django123'
    new_password = 'Django321'

    url_signup = reverse('account:signup')
    plain_url_activate = 'account:activate'

    @classmethod
    def setUpClass(cls):
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

    def _create_admin_user(self, email=None, password=None):
        token, id = self._create_activated_user(email, password)
        user = get_user_model().objects.get(id=id)
        user.is_staff = True
        user.save()
        return token, id
