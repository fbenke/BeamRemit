import copy

from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from pricing.models import Pricing, ExchangeRate, Comparison, Limit,\
    get_current_object, get_current_object_by_site

from unittest import skip


class PricingAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_pricing(self):
        no_pricings = Pricing.objects.all().count()

        response = self.client.post(reverse('admin:pricing_pricing_add'), data=self.default_beam_pricing)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Pricing.objects.all().count(), no_pricings + 1)
        pricing = get_current_object_by_site(Pricing, Site.objects.get(id=0))
        self.assertEqual(pricing.markup, 0.03)
        self.assertEqual(pricing.fee, 1)
        self.assertEqual(pricing.fee_currency, 'GBP')
        self.assertEqual(pricing.site.id, 0)

        response = self.client.post(reverse('admin:pricing_pricing_add'), data=self.default_bae_pricing)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Pricing.objects.all().count(), no_pricings + 2)
        pricing = get_current_object_by_site(Pricing, Site.objects.get(id=1))
        self.assertEqual(pricing.markup, 0.02)
        self.assertEqual(pricing.fee, 0)
        self.assertEqual(pricing.fee_currency, 'USD')
        self.assertEqual(pricing.site.id, 1)

    def test_add_pricing_validaton_error(self):
        new_pricing = copy.deepcopy(self.default_beam_pricing)
        new_pricing['markup'] = 10
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=new_pricing)
        self.assertContains(response, 'Markup has to be a value between 0 and 1')


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
        exchange_rate = get_current_object(ExchangeRate)
        self.assertEqual(exchange_rate.gbp_ghs, 5.3)
        self.assertEqual(exchange_rate.gbp_usd, 1.6)
        self.assertEqual(exchange_rate.gbp_sll, 7040)


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

        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=self.default_beam_limit
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), no_limits + 1)

        limit = get_current_object_by_site(Limit, Site.objects.get(id=0))
        self.assertEqual(limit.transaction_min, 2)
        self.assertEqual(limit.transaction_max, 1000)
        self.assertEqual(limit.user_limit_basic, 40)
        self.assertEqual(limit.user_limit_complete, 500)
        self.assertEqual(limit.sending_currency, 'GBP')
        self.assertEqual(limit.receiving_currency, 'GHS')
        self.assertEqual(limit.site.id, 0)

        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=self.default_bae_limit
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), no_limits + 2)

        limit = get_current_object_by_site(Limit, Site.objects.get(id=1))
        self.assertEqual(limit.transaction_min, 1)
        self.assertEqual(limit.transaction_max, 100)
        self.assertEqual(limit.user_limit_basic, 37)
        self.assertEqual(limit.user_limit_complete, 324)
        self.assertEqual(limit.sending_currency, 'USD')
        self.assertEqual(limit.receiving_currency, 'SLL')
        self.assertEqual(limit.site.id, 1)

    def test_add_limit_validaton_error(self):
        new_limit = copy.deepcopy(self.default_beam_limit)
        new_limit['transaction_min'] = 1000
        response = self.client.post(reverse('admin:pricing_limit_add'), data=new_limit)
        self.assertContains(response, 'Minimum amount must be smaller than maximum amount.')


class PricingAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:current')

    def test_get_current_pricing(self):

        beam_pricing = self._create_default_pricing_beam()
        bae_pricing = self._create_default_pricing_bae()
        exchange_rate = self._create_default_exchange_rate()
        comparison = self._create_comparison()
        state = self._create_state(site_id=0)
        state = self._create_state(site_id=1)

        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pricing_id'], beam_pricing.id)
        self.assertEqual(response.data['exchange_rate_id'], exchange_rate.id)
        self.assertEqual(response.data['fee'], 2.9)
        self.assertEqual(response.data['rate'], 5.141)
        self.assertEqual(response.data['fee_currency'], 'GBP')
        self.assertEqual(response.data['comparison'], comparison.price_comparison)
        self.assertEqual(response.data['comparison_retrieved'], comparison.start)
        self.assertEqual(response.data['operation_mode'], state.state)

        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pricing_id'], bae_pricing.id)
        self.assertEqual(response.data['exchange_rate_id'], exchange_rate.id)
        self.assertEqual(response.data['fee'], 1.2)
        self.assertEqual(response.data['rate'], 4356)
        self.assertEqual(response.data['fee_currency'], 'USD')
        self.assertEqual(response.data['comparison'], comparison.price_comparison)
        self.assertEqual(response.data['comparison_retrieved'], comparison.start)
        self.assertEqual(response.data['operation_mode'], state.state)


class LimitAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:limit')

    def setUp(self):
        self._create_default_exchange_rate()

    def test_get_limit(self):
        self._create_default_pricing_beam()
        self._create_default_limit_beam()
        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.data['user_limit_basic'], 40)
        self.assertEqual(response.data['user_limit_complete'], 500)
        self.assertEqual(response.data['transaction_min'], 2)
        self.assertEqual(response.data['transaction_max'], 1000)
        self.assertEqual(response.data['sending_currency'], 'GBP')
        self.assertEqual(response.data['receiving_currency'], 'GHS')
        self.assertEqual(response.data['transaction_min_receiving'], 10.282)
        self.assertEqual(response.data['transaction_max_receiving'], 5141)

    def test_get_limit_bae(self):
        self._create_default_pricing_bae()
        self._create_default_limit_bae()
        response = self.client.get(self.url_get_current, {}, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.data['user_limit_basic'], 50)
        self.assertEqual(response.data['user_limit_complete'], 600)
        self.assertEqual(response.data['transaction_min'], 3)
        self.assertEqual(response.data['transaction_max'], 600)
        self.assertEqual(response.data['sending_currency'], 'USD')
        self.assertEqual(response.data['receiving_currency'], 'SLL')
        self.assertEqual(response.data['transaction_min_receiving'], 13068)
        self.assertEqual(response.data['transaction_max_receiving'], 2613600)


@skip
class PricingConversionTests(TestCase, TestUtils):

    def setUp(self):
        self.exchange_rate = self._create_default_exchange_rate()
        self.pricing_beam = self._create_default_pricing_beam()
        self.pricing_bae = self._create_default_pricing_bae()

    def test_conversion_gbp(self):
        self.assertEqual(self.pricing_beam.calculate_received_amount(12, 'GBP', 'GH'), 61.7)
        self.assertEqual(self.pricing_beam.calculate_received_amount(5, 'GBP', 'SL'), 34150)
        self.assertEqual(self.pricing_bae.calculate_received_amount(12, 'GBP', 'GH'), 63)
        self.assertEqual(self.pricing_bae.calculate_received_amount(5, 'GBP', 'SL'), 34850)

    def test_conversion_usd(self):
        self.assertEqual(self.pricing_beam.calculate_received_amount(18, 'USD', 'GH'), 57.9)
        self.assertEqual(self.pricing_beam.calculate_received_amount(7, 'USD', 'SL'), 29880)
        self.assertEqual(self.pricing_beam.calculate_received_amount(18, 'USD', 'SL'), 76830)
        self.assertEqual(self.pricing_bae.calculate_received_amount(18, 'USD', 'GH'), 59.1)
        self.assertEqual(self.pricing_bae.calculate_received_amount(7, 'USD', 'SL'), 30500)
        self.assertEqual(self.pricing_bae.calculate_received_amount(18, 'USD', 'SL'), 78410)

    def test_convert_to_base_currency(self):
        self.assertEqual(self.exchange_rate.convert_to_base_currency(3.245, 'GBP'), 3.245)
        self.assertEqual(self.exchange_rate.convert_to_base_currency(20, 'USD'), 12.5)
