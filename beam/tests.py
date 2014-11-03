from django.contrib.auth.models import User


class TestUtils(object):

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 200)])

    default_username = 'falk'
    default_password = 'Django123'
    default_new_password = 'Django321'
    default_invalid_password = 'Invd'
    default_identification_issue_date = '2000-01-01'
    default_identification_expiry_date = '2020-01-01'
    default_identification_number = 'C3J3ZZ7VP'

    default_pricing = {
        'markup': 0.03,
        'fee_usd': 0,
        'fee_gbp': 1,
        'gbp_ghs': 5.3,
        'gbp_usd': 1.6,
        'gbp_sll': 7040
    }

    default_profile = {
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

    def _create_admin_user(self, email=None):
        if not email:
            email = self.emails.next()
        return User.objects.create_superuser(
            username=self.default_username,
            email=email,
            password=self.default_password)
