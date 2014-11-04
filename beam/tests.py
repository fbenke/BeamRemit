from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from pricing.models import Pricing, Comparison, end_previous_object


class TestUtils(object):

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 200)])

    default_username = 'falk'
    default_password = 'Django123'
    default_new_password = 'Django321'
    default_invalid_password = 'Invd'
    default_identification_issue_date = '2000-01-01'
    default_identification_expiry_date = '2020-01-01'
    default_identification_number = 'C3J3ZZ7VP'

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

    default_pricing = {
        'markup': 0.03,
        'fee_usd': 0,
        'fee_gbp': 1,
        'gbp_ghs': 5.3,
        'gbp_usd': 1.6,
        'gbp_sll': 7040
    }

    default_limit = {
        'transaction_min_gbp': 1,
        'transaction_max_gbp': 500,
        'user_limit_basic_gbp': 40,
        'user_limit_complete_gbp': 500
    }

    default_comparison = '{"gbpGhs": {"wu": 5.0932009, "mg": 5.158165}}'

    url_get_current = reverse('pricing:current')

    def _create_admin_user(self, email=None):
        if not email:
            email = self.emails.next()
        return User.objects.create_superuser(
            username=self.default_username,
            email=email,
            password=self.default_password)

    def _create_pricing(self):

        pricing = Pricing(
            markup=self.default_pricing['markup'],
            fee_usd=self.default_pricing['fee_usd'],
            fee_gbp=self.default_pricing['fee_gbp'],
            gbp_ghs=self.default_pricing['gbp_ghs'],
            gbp_usd=self.default_pricing['gbp_usd'],
            gbp_sll=self.default_pricing['gbp_sll']
        )
        end_previous_object(Pricing)
        pricing.save()
        return pricing

    def _create_comparison(self):
        comparison = Comparison(price_comparison=self.default_comparison)
        end_previous_object(Comparison)
        comparison.save()
        return comparison
