import copy

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from pricing.models import Pricing, Comparison, Limit, get_current_object


class PricingAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_pricing(self):

        self.assertEqual(Pricing.objects.all().count(), 0)
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=self.default_pricing)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Pricing.objects.all().count(), 1)

        pricing = get_current_object(Pricing)
        self.assertEqual(self.default_pricing['markup'], pricing.markup)
        self.assertEqual(self.default_pricing['fee_usd'], pricing.fee_usd)
        self.assertEqual(self.default_pricing['fee_gbp'], pricing.fee_gbp)
        self.assertEqual(self.default_pricing['gbp_ghs'], pricing.gbp_ghs)
        self.assertEqual(self.default_pricing['gbp_usd'], pricing.gbp_usd)
        self.assertEqual(self.default_pricing['gbp_sll'], pricing.gbp_sll)

    def test_add_pricing_validaton_error(self):
        new_pricing = copy.deepcopy(self.default_pricing)
        new_pricing['markup'] = 10
        response = self.client.post(reverse('admin:pricing_pricing_add'), data=new_pricing)
        self.assertContains(response, 'Markup has to be a value between 0 and 1')


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

        self.assertEqual(Limit.objects.all().count(), 0)
        response = self.client.post(
            reverse('admin:pricing_limit_add'),
            data=self.default_limit
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Limit.objects.all().count(), 1)

        limit = get_current_object(Limit)
        self.assertEqual(limit.transaction_min_gbp, self.default_limit['transaction_min_gbp'])
        self.assertEqual(limit.transaction_max_gbp, self.default_limit['transaction_max_gbp'])
        self.assertEqual(limit.user_limit_basic_gbp, self.default_limit['user_limit_basic_gbp'])
        self.assertEqual(limit.user_limit_complete_gbp, self.default_limit['user_limit_complete_gbp'])

    def test_add_limit_validaton_error(self):
        new_limt = self.default_limit
        new_limt['transaction_min_gbp'] = 1000
        response = self.client.post(reverse('admin:pricing_limit_add'), data=new_limt)
        self.assertContains(response, 'Minimum amount must be smaller than maximum amount.')


class PricingAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:current')

    def test_get_current_pricing(self):

        pricing = self._create_pricing()
        comparison = self._create_comparison()
        state = self._create_state()

        response = self.client.get(self.url_get_current)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pricing_id'], pricing.id)
        self.assertEqual(response.data['beam_fee_usd'], pricing.fee_usd)
        self.assertEqual(response.data['beam_fee_gbp'], pricing.fee_gbp)
        self.assertEqual(response.data['comparison'], comparison.price_comparison)
        self.assertEqual(response.data['comparison_retrieved'], comparison.start)
        self.assertEqual(response.data['operation_mode'], state.state)
        self.assertEqual(response.data['beam_rate_ghs'], 5.141)
        self.assertEqual(response.data['beam_rate_sll'], 6828.8)
        self.assertEqual(response.data['beam_rate_usd'], 1.6)


class LimitAPITests(APITestCase, TestUtils):

    url_get_current = reverse('pricing:limit')

    def test_get_limit(self):
        limit = self._create_limit()
        self._create_pricing()

        response = self.client.get(self.url_get_current)
        self.assertEqual(response.data['user_limit_basic_gbp'], limit.user_limit_basic_gbp)
        self.assertEqual(response.data['user_limit_complete_gbp'], limit.user_limit_complete_gbp)
        self.assertEqual(response.data['transaction_min_gbp'], limit.transaction_min_gbp)
        self.assertEqual(response.data['transaction_max_gbp'], limit.transaction_max_gbp)
        self.assertEqual(response.data['user_limit_basic_usd'], 64)
        self.assertEqual(response.data['user_limit_complete_usd'], 800)
        self.assertEqual(response.data['transaction_min_usd'], 3.2)
        self.assertEqual(response.data['transaction_max_usd'], 1600)
        self.assertEqual(response.data['transaction_min_sll'], 13657.6)
        self.assertEqual(response.data['transaction_max_sll'], 6828800)
        self.assertEqual(response.data['transaction_min_ghs'], 10.282)
        self.assertEqual(response.data['transaction_max_ghs'], 5141)


class PricingConversionTests(TestCase, TestUtils):

    def setUp(self):
        self.pricing = self._create_pricing()

    def test_conversion_gbp(self):
        self.assertEqual(self.pricing.calculate_received_amount(12, 'GBP', 'GH'), 61.7)
        self.assertEqual(self.pricing.calculate_received_amount(5, 'GBP', 'SL'), 34150)

    def test_conversion_usd(self):
        self.assertEqual(self.pricing.calculate_received_amount(18, 'USD', 'GH'), 57.9)
        self.assertEqual(self.pricing.calculate_received_amount(7, 'USD', 'SL'), 29880)
