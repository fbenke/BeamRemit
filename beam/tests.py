from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone

from userena.models import UserenaSignup
from userena import settings as userena_settings

from rest_framework.authtoken.models import Token

from account.models import BeamProfile as Profile

from beam.utils.angular_requests import get_site_by_request

from pricing.models import Pricing, ExchangeRate, Comparison, Limit,\
    end_previous_object, end_previous_object_by_site

from state.models import State

from transaction.models import Recipient, Transaction


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
    default_recipient_first_name = 'Nikunj'
    default_recipient_last_name = 'Hand'
    default_recipient_phone_number = '0245025019'

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
        'fee': 1,
        'fee_currency': 'GBP',
        'site': 0
    }

    default_bae_pricing = {
        'markup': 0.02,
        'fee': 0,
        'fee_currency': 'USD',
        'site': 1
    }

    default_exchange_rate = {
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

    def _create_pricing(self, markup, fee, fee_currency, site_id):
        site = Site.objects.get(id=site_id)
        pricing = Pricing(
            markup=markup,
            fee=fee,
            fee_currency=fee_currency,
            site=site
        )
        end_previous_object_by_site(Pricing, site)
        pricing.save()
        return pricing

    def _create_default_pricing(self):
        return self._create_pricing(
            markup=self.default_pricing['markup'],
            fee=self.default_pricing['fee'],
            fee_currency=self.default_pricing['fee_currency'],
            site_id=self.default_pricing['site']
        )

    def _create_exchange_rate(self, gbp_ghs, gbp_usd, gbp_sll):
        exchange_rate = ExchangeRate(
            gbp_ghs=gbp_ghs,
            gbp_usd=gbp_usd,
            gbp_sll=gbp_sll
        )
        end_previous_object(ExchangeRate)
        exchange_rate.save()
        return exchange_rate

    def _create_default_exchange_rate(self):
        return self._create_exchange_rate(
            gbp_ghs=self.default_exchange_rate['gbp_ghs'],
            gbp_usd=self.default_exchange_rate['gbp_usd'],
            gbp_sll=self.default_exchange_rate['gbp_sll']
        )

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

    def _create_default_limit(self):
        limit = Limit(
            transaction_min_gbp=self.default_limit['transaction_min_gbp'],
            transaction_max_gbp=self.default_limit['transaction_max_gbp'],
            user_limit_basic_gbp=self.default_limit['user_limit_basic_gbp'],
            user_limit_complete_gbp=self.default_limit['user_limit_complete_gbp']
        )
        end_previous_object(Limit)
        limit.save()
        return limit

    def _create_transaction(self, sender, pricing, sent_amount, sent_currency,
                            received_amount, receiving_country):

        recipient = Recipient(
            first_name=self.default_recipient_first_name,
            last_name=self.default_recipient_last_name,
            phone_number=self.default_recipient_phone_number)

        recipient.save()
        transaction = Transaction(
            recipient=recipient,
            sender=sender,
            pricing=pricing,
            sent_amount=sent_amount,
            sent_currency=sent_currency,
            received_amount=received_amount,
            receiving_country=receiving_country,
            state='PAID',
            paid_at=timezone.now()
        )
        transaction.save()
        return transaction

    def _create_default_transaction(self, sender, pricing):

        return self._create_transaction(
            sender=sender,
            pricing=pricing,
            sent_amount=10,
            sent_currency='GBP',
            received_amount=53,
            receiving_country='GH',
        )


class SiteMappingTests(TestCase, TestUtils):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_site_by_request(self):
        dummy_request = self.factory.get('/')
        dummy_request.META['HTTP_REFERER'] = 'http://dev.beamremit.com/'
        site = get_site_by_request(dummy_request)
        self.assertIsNotNone(site)
        self.assertEqual(site.id, 0)
        self.assertEqual(site.domain, 'dev.beamremit.com')

        dummy_request = self.factory.get('/')
        dummy_request.META['HTTP_REFERER'] = 'http://dev.bitcoinagainstebola.org/'
        site = get_site_by_request(dummy_request)
        self.assertIsNotNone(site)
        self.assertEqual(site.id, 1)
        self.assertEqual(site.domain, 'dev.bitcoinagainstebola.org')

    def test_get_site_by_request_fail(self):
        dummy_request = self.factory.get('/')
        dummy_request.META['HTTP_REFERER'] = 'foo'
        site = get_site_by_request(dummy_request)
        self.assertIsNotNone(site)
        self.assertEqual(site.id, 0)
