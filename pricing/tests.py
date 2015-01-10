from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from pricing.models import Pricing, ExchangeRate, Comparison, Limit, Fee,\
    get_current_pricing, get_current_fee, get_current_exchange_rate, get_current_limit

# from unittest import skip


class PricingAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_pricing(self):
        no_pricings = Pricing.objects.all().count()

        beam_pricing = {'markup': 0.03, 'site': 0}
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=beam_pricing)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Pricing.objects.all().count(), no_pricings + 1)
        pricing = get_current_pricing(Site.objects.get(id=0))
        self.assertEqual(pricing.markup, 0.03)
        self.assertEqual(pricing.site.id, 0)

        bae_pricing = {'markup': 0.02, 'site': 1}
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=bae_pricing)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Pricing.objects.all().count(), no_pricings + 2)
        pricing = get_current_pricing(Site.objects.get(id=1))
        self.assertEqual(pricing.markup, 0.02)
        self.assertEqual(pricing.site.id, 1)

    def test_add_pricing_validaton_error(self):
        beam_pricing = {'markup': 10, 'site': 0}
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=beam_pricing)
        self.assertContains(response, 'Markup has to be a value between 0 and 1')


class FeeAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_fee(self):
        no_fees = Fee.objects.all().count()

        beam_fee_eur = {'amount': 1, 'currency': 'EUR', 'site': 0}
        beam_fee_gbp = {'amount': 2, 'currency': 'GBP', 'site': 0}
        bae_fee_usd = {'amount': 3, 'currency': 'USD', 'site': 1}

        response = self.client.post(reverse('admin:pricing_fee_add'), data=beam_fee_eur)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response = self.client.post(reverse('admin:pricing_fee_add'), data=beam_fee_gbp)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response = self.client.post(reverse('admin:pricing_fee_add'), data=bae_fee_usd)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(Fee.objects.all().count(), no_fees + 3)

        fee = get_current_fee(Site.objects.get(id=0), 'EUR')
        self.assertEqual(fee.amount, 1)
        self.assertEqual(fee.site.id, 0)
        self.assertEqual(fee.currency, 'EUR')

        fee = get_current_fee(Site.objects.get(id=0), 'GBP')
        self.assertEqual(fee.amount, 2)
        self.assertEqual(fee.site.id, 0)
        self.assertEqual(fee.currency, 'GBP')

        fee = get_current_fee(Site.objects.get(id=1), 'USD')
        self.assertEqual(fee.amount, 3)
        self.assertEqual(fee.site.id, 1)
        self.assertEqual(fee.currency, 'USD')

    def test_add_pricing_validaton_error(self):
        beam_fee = {'fee': 1, 'currency': 'USD', 'site': 0}
        response = self.client.post(reverse('admin:pricing_fee_add'), data=beam_fee)
        self.assertContains(response, 'Sending currency not supported for that Site.')


class ExchangeRateAdminTests(TestCase, TestUtils):
    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_currency(self):
        no_exchange_rates = ExchangeRate.objects.all().count()

        response = self.client.post(reverse('admin:pricing_exchangerate_add'), data=self.default_exchange_rate)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(ExchangeRate.objects.all().count(), no_exchange_rates + 1)
        exchange_rate = get_current_exchange_rate()
        self.assertEqual(exchange_rate.gbp_ghs, 5.3)
        self.assertEqual(exchange_rate.gbp_usd, 1.6)
        self.assertEqual(exchange_rate.gbp_sll, 7040)
        self.assertEqual(exchange_rate.gbp_eur, 1.25)


class ComparisonAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_comparison(self):

        self.assertEqual(Comparison.objects.all().count(), 0)
        response = self.client.post(
            reverse('admin:pricing_comparison_add'),
            data={'price_comparison': self.default_comparison}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Comparison.objects.all().count(), 1)


class LimitAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_limit(self):

        no_limits = Limit.objects.all().count()

        beam_limit_eur = {
            'transaction_min': 2,
            'transaction_max': 1000,
            'sending_currency': 'EUR',
            'user_limit_basic': 40,
            'user_limit_complete': 500,
            'site': 0
        }

        beam_limit_gbp = {
            'transaction_min': 1,
            'transaction_max': 800,
            'sending_currency': 'GBP',
            'user_limit_basic': 30,
            'user_limit_complete': 400,
            'site': 0
        }

        bae_limit_usd = {
            'transaction_min': 1,
            'transaction_max': 100,
            'user_limit_basic': 37,
            'sending_currency': 'USD',
            'user_limit_complete': 324,
            'site': 1
        }

        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=beam_limit_eur
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), no_limits + 1)

        limit = get_current_limit(site=Site.objects.get(id=0), currency='EUR')
        self.assertEqual(limit.transaction_min, 2)
        self.assertEqual(limit.transaction_max, 1000)
        self.assertEqual(limit.user_limit_basic, 40)
        self.assertEqual(limit.user_limit_complete, 500)
        self.assertEqual(limit.sending_currency, 'EUR')
        self.assertEqual(limit.receiving_currency, 'GHS')
        self.assertEqual(limit.site.id, 0)

        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=beam_limit_gbp
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), no_limits + 2)

        limit = get_current_limit(site=Site.objects.get(id=0), currency='GBP')
        self.assertEqual(limit.transaction_min, 1)
        self.assertEqual(limit.transaction_max, 800)
        self.assertEqual(limit.user_limit_basic, 30)
        self.assertEqual(limit.user_limit_complete, 400)
        self.assertEqual(limit.sending_currency, 'GBP')
        self.assertEqual(limit.receiving_currency, 'GHS')
        self.assertEqual(limit.site.id, 0)

        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=bae_limit_usd
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), no_limits + 3)

        limit = get_current_limit(site=Site.objects.get(id=1), currency='USD')
        self.assertEqual(limit.transaction_min, 1)
        self.assertEqual(limit.transaction_max, 100)
        self.assertEqual(limit.user_limit_basic, 37)
        self.assertEqual(limit.user_limit_complete, 324)
        self.assertEqual(limit.sending_currency, 'USD')
        self.assertEqual(limit.receiving_currency, 'SLL')
        self.assertEqual(limit.site.id, 1)

    def test_add_limit_validaton_error(self):
        bae_limit_usd = {
            'transaction_min': 101,
            'transaction_max': 100,
            'user_limit_basic': 37,
            'sending_currency': 'USD',
            'user_limit_complete': 324,
            'site': 1
        }
        response = self.client.post(reverse('admin:pricing_limit_add'), data=bae_limit_usd)
        self.assertContains(response, 'Minimum amount must be smaller than maximum amount.')


class PricingAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:current')

    def test_get_current_pricing(self):

        fee_beam_eur = self._create_fee(amount=0.3, currency='EUR', site_id=0)
        fee_beam_gbp = self._create_fee(amount=0.2, currency='GBP', site_id=0)
        fee_bae_usd = self._create_fee(amount=0, currency='USD', site_id=1)
        beam_pricing = self._create_pricing(markup=0.03, site_id=0)
        bae_pricing = self._create_pricing(markup=0.02, site_id=1)
        exchange_rate = self._create_default_exchange_rate()
        comparison = self._create_comparison()
        state = self._create_state(site_id=0)
        state = self._create_state(site_id=1)

        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pricing_id'], beam_pricing.id)
        self.assertEqual(response.data['exchange_rate_id'], exchange_rate.id)
        self.assertEqual(response.data['default_currency'], 'EUR')
        self.assertEqual(response.data['fees']['EUR']['rate'], 0.3)
        self.assertEqual(response.data['fees']['EUR']['id'], fee_beam_eur.id)
        self.assertEqual(response.data['fees']['GBP']['rate'], 0.2)
        self.assertEqual(response.data['fees']['GBP']['id'], fee_beam_gbp.id)
        self.assertEqual(response.data['rates']['GBP'], 5.141)
        self.assertEqual(response.data['rates']['EUR'], 4.1128)
        self.assertEqual(response.data['comparison'], comparison.price_comparison)
        self.assertEqual(response.data['comparison_retrieved'], comparison.start)
        self.assertEqual(response.data['operation_mode'], state.state)

        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pricing_id'], bae_pricing.id)
        self.assertEqual(response.data['exchange_rate_id'], exchange_rate.id)
        self.assertEqual(response.data['fees']['USD']['rate'], 0)
        self.assertEqual(response.data['fees']['USD']['id'], fee_bae_usd.id)
        self.assertEqual(response.data['rates']['USD'], 4312)
        self.assertEqual(response.data['comparison'], comparison.price_comparison)
        self.assertEqual(response.data['comparison_retrieved'], comparison.start)
        self.assertEqual(response.data['operation_mode'], state.state)


class LimitAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:limit')

    def setUp(self):
        self._create_default_exchange_rate()

    def test_get_limit(self):

        self._create_pricing(markup=0.03, site_id=0)

        self._create_limit(
            transaction_min=2,
            transaction_max=1000,
            user_limit_basic=40,
            user_limit_complete=500,
            site_id=0,
            sending_currency='GBP'
        )

        self._create_limit(
            transaction_min=1,
            transaction_max=1200,
            user_limit_basic=50,
            user_limit_complete=600,
            site_id=0,
            sending_currency='EUR'
        )

        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.beamremit.com/')

        i = 0

        for limit in response.data:

            if limit['sendingCurrency'] == 'GBP':
                i = i + 1
                self.assertEqual(limit['userLimitBasic'], 40)
                self.assertEqual(limit['userLimitComplete'], 500)
                self.assertEqual(limit['transactionMin'], 2)
                self.assertEqual(limit['transactionMax'], 1000)
                self.assertEqual(limit['receivingCurrency'], 'GHS')
                self.assertEqual(limit['transactionMinReceiving'], 10.282)
                self.assertEqual(limit['transactionMaxReceiving'], 5141)

            elif limit['sendingCurrency'] == 'EUR':
                i = i + 1
                self.assertEqual(limit['userLimitBasic'], 50)
                self.assertEqual(limit['userLimitComplete'], 600)
                self.assertEqual(limit['transactionMin'], 1)
                self.assertEqual(limit['transactionMax'], 1200)
                self.assertEqual(limit['receivingCurrency'], 'GHS')
                self.assertEqual(limit['transactionMinReceiving'], 4.1128)
                self.assertEqual(limit['transactionMaxReceiving'], 4935.36)

        self.assertEqual(i, 2)

    def test_get_limit_bae(self):

        self._create_pricing(markup=0.02, site_id=1)

        self._create_limit(
            transaction_min=3,
            transaction_max=600,
            user_limit_basic=50,
            user_limit_complete=700,
            site_id=1,
            sending_currency='USD'
        )
        
        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.data[0]['userLimitBasic'], 50)
        self.assertEqual(response.data[0]['userLimitComplete'], 700)
        self.assertEqual(response.data[0]['transactionMin'], 3)
        self.assertEqual(response.data[0]['transactionMax'], 600)
        self.assertEqual(response.data[0]['sendingCurrency'], 'USD')
        self.assertEqual(response.data[0]['receivingCurrency'], 'SLL')
        self.assertEqual(response.data[0]['transactionMinReceiving'], 12936)
        self.assertEqual(response.data[0]['transactionMaxReceiving'], 2587200)


class PricingConversionTests(TestCase, TestUtils):

    def setUp(self):
        self.exchange_rate = self._create_default_exchange_rate()

    def test_get_exchange_rate(self):
        self.assertEqual(self.exchange_rate.get_exchange_rate('GBP', 'USD'), 1.6)
        self.assertEqual(self.exchange_rate.get_exchange_rate('GBP', 'SLL'), 7040)
        self.assertEqual(self.exchange_rate.get_exchange_rate('GBP', 'GHS'), 5.3)
        self.assertEqual(self.exchange_rate.get_exchange_rate('GBP', 'EUR'), 1.25)
        self.assertEqual(self.exchange_rate.get_exchange_rate('USD', 'GBP'), 0.625)
        self.assertEqual(self.exchange_rate.get_exchange_rate('USD', 'SLL'), 4400)
        self.assertTrue(abs(self.exchange_rate.get_exchange_rate('USD', 'GHS') - 3.3125) < 0.00001)
        self.assertEqual(self.exchange_rate.get_exchange_rate('USD', 'EUR'), 0.78125)
        self.assertEqual(self.exchange_rate.get_exchange_rate('EUR', 'USD'), 1.28)
        self.assertEqual(self.exchange_rate.get_exchange_rate('EUR', 'SLL'), 5632)
        self.assertEqual(self.exchange_rate.get_exchange_rate('EUR', 'GHS'), 4.24)
        self.assertEqual(self.exchange_rate.get_exchange_rate('EUR', 'GBP'), 0.8)
    
    def test_get_exchange_rate_by_site(self):
        rates = self.exchange_rate.exchange_rates(Site.objects.get(id=0))
        self.assertEqual(rates['GBP'], 5.3)
        self.assertEqual(rates['EUR'], 4.24)
        rates = self.exchange_rate.exchange_rates(Site.objects.get(id=1))
        self.assertEqual(rates['USD'], 4400)

    def test_get_gbp_to_currency(self):
        self.assertEqual(self.exchange_rate._get_gbp_to_currency('GBP'), 1)
        self.assertEqual(self.exchange_rate._get_gbp_to_currency('USD'), 1.6)
        self.assertEqual(self.exchange_rate._get_gbp_to_currency('SLL'), 7040)
        self.assertEqual(self.exchange_rate._get_gbp_to_currency('GHS'), 5.3)
        self.assertEqual(self.exchange_rate._get_gbp_to_currency('EUR'), 1.25)

    def test_exchange_amount(self):
        self.assertTrue(abs(self.exchange_rate.exchange_amount(12, 'GBP', 'USD') - 19.2) < 0.00001)
        self.assertEqual(self.exchange_rate.exchange_amount(13, 'GBP', 'SLL'), 91520)
        self.assertEqual(self.exchange_rate.exchange_amount(14, 'GBP', 'GHS'), 74.2)
        self.assertEqual(self.exchange_rate.exchange_amount(15, 'USD', 'GBP'), 9.375)
        self.assertEqual(self.exchange_rate.exchange_amount(16, 'USD', 'SLL'), 70400)
        self.assertTrue(abs(self.exchange_rate.exchange_amount(17, 'USD', 'GHS') - 56.3125) < 0.00001)

    def test_exchange_rates_with_markup(self):
        pricing_beam = self._create_pricing(markup=0.03, site_id=0)
        self.assertEqual(pricing_beam.exchange_rates['EUR'], 4.1128)
        self.assertEqual(pricing_beam.exchange_rate('EUR'), 4.1128)
        self.assertEqual(pricing_beam.exchange_rates['GBP'], 5.141)
        self.assertEqual(pricing_beam.exchange_rate('GBP'), 5.141)
        pricing_bae = self._create_pricing(markup=0.02, site_id=1)
        self.assertEqual(pricing_bae.exchange_rates['USD'], 4312)
        self.assertEqual(pricing_bae.exchange_rate('USD'), 4312)
