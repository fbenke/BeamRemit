from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase

from userena.models import UserenaSignup
from userena.utils import get_user_model


class BeamAPITestCase(APITestCase):

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 100)])
    password = 'Django123'
    new_password = 'Django321'
    invalid_password = 'schatzi'

    url_signup = reverse('account:signup')
    url_profile = reverse('account:profile')
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
            'acceptedPrivacyPolicy': True,
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

    def _create_user_with_profile(self, email=None, password=None):
        token, id = self._create_activated_user(email=email, password=password)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        data = {
            'firstName': 'Falk',
            'lastName': 'Benke',
            'profile': {
                'country': 'DE',
                'date_of_birth': '1985-10-04',
                'city': 'Berlin',
                'street': 'Platz der Vereinten Nationen 23',
                'post_code': '10249'
            }
        }
        self.client.patch(self.url_profile, data)
        return token, id

    def _create_fully_verified_user(self, email=None, password=None):
        token, id = self._create_activated_user(email=email, password=password)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        user = get_user_model().objects.get(id=id)
        user.profile.identification_state = 'VER'
        user.profile.identification_issue_date = '2000-01-01'
        user.profile.identification_expiry_date = '2010-01-01'
        user.profile.identification_number = 'C3J3'
        user.profile.proof_of_residence_state = 'VER'
        user.profile.save()
        return token, id
