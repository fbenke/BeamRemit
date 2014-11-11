from django.contrib.auth.models import User

from userena.models import UserenaSignup
from userena import settings as userena_settings

from rest_framework.authtoken.models import Token

from account.models import BeamProfile as Profile

from pricing.models import Pricing, Comparison, Limit, end_previous_object

from state.models import State


class TestUtils(object):

    emails = iter(['test{}@mail.com'.format(k) for k in xrange(1, 200)])
    usernames = iter(['user{}'.format(k) for k in xrange(1, 200)])

    default_username = 'falk'
    default_password = 'Django123'
    default_new_password = 'Django321'
    default_invalid_password = 'Invd'
    default_identification_issue_date = '2000-01-01'
    default_identification_expiry_date = '2020-01-01'
    default_identification_number = 'C3J3ZZ7VP'

    default_profile = {
        'first_name': 'Falk',
        'last_name': 'Benke',
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
        'transaction_min_gbp': 2,
        'transaction_max_gbp': 1000,
        'user_limit_basic_gbp': 40,
        'user_limit_complete_gbp': 500
    }

    default_comparison = '{"gbpGhs": {"wu": 5.0932009, "mg": 5.158165}}'

    default_id_document = {
        'document': Profile.IDENTIFICATION,
        'issue': '2012-2-3',
        'expiry': '2022-2-3',
        'number': 'C3J3ZZ7VP'
    }

    def _create_inactive_user(self, email=None, password=None):
        if email is None:
            email = self.emails.next()

        if password is None:
            password = self.default_password

        return UserenaSignup.objects.create_user(
            username=self.usernames.next(),
            email=email,
            password=password,
            active=False,
            send_email=False
        )

    def _create_activated_user(self, email=None, password=None):
        user = self._create_inactive_user(email, password)
        user.userena_signup.activation_key = userena_settings.USERENA_ACTIVATED
        user.is_active = True
        user.save()
        user.userena_signup.save()
        return user

    def _create_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

    def _create_user_with_profile(self, email=None, password=None):
        user = self._create_activated_user(email=email, password=password)
        user.first_name = self.default_profile['first_name']
        user.last_name = self.default_profile['last_name']
        user.profile.country = self.default_profile['profile']['country']
        user.profile.date_of_birth = self.default_profile['profile']['date_of_birth']
        user.profile.city = self.default_profile['profile']['city']
        user.profile.street = self.default_profile['profile']['street']
        user.profile.post_code = self.default_profile['profile']['post_code']
        user.profile.save()
        user.save()
        return user

    def _create_fully_verified_user(self, email=None, password=None):
        user = self._create_user_with_profile(email=email, password=password)
        user.profile.identification_state = Profile.VERIFIED
        user.profile.identification_issue_date = self.default_identification_issue_date
        user.profile.identification_expiry_date = self.default_identification_expiry_date
        user.profile.identification_number = self.default_identification_number
        user.profile.proof_of_residence_state = Profile.VERIFIED
        user.profile.save()
        return user

    def _create_user_with_uploaded_documents(self, email=None, password=None):
        user = self._create_user_with_profile(email=email, password=password)
        user.profile.identification_state = Profile.UPLOADED
        user.profile.identification_issue_date = self.default_identification_issue_date
        user.profile.identification_expiry_date = self.default_identification_expiry_date
        user.profile.identification_number = self.default_identification_number
        user.profile.proof_of_residence_state = Profile.UPLOADED
        user.profile.save()
        return user

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

    def _create_state(self, state=None):
        if not state:
            state = State.RUNNING
        app_state = State(state=state)
        end_previous_object(State)
        app_state.save()
        return app_state

    def _create_limit(self):
        limit = Limit(
            transaction_min_gbp=self.default_limit['transaction_min_gbp'],
            transaction_max_gbp=self.default_limit['transaction_max_gbp'],
            user_limit_basic_gbp=self.default_limit['user_limit_basic_gbp'],
            user_limit_complete_gbp=self.default_limit['user_limit_complete_gbp']
        )
        end_previous_object(Limit)
        limit.save()
        return limit
