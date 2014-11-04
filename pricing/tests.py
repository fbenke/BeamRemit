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
        new_pricing = self.default_pricing
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

    def test_add_limit_validaton_error(self):
        new_limt = self.default_limit
        new_limt['transaction_min_gbp'] = 1000
        response = self.client.post(reverse('admin:pricing_limit_add'), data=new_limt)
        self.assertContains(response, 'Minimum amount must be smaller than maximum amount.')

# class PricingAPITests(APITestCase, TestUtils):

#     def test_get_current_pricing(self):

#         pricing = self._create_pricing()
#         comparison = self._create_comparison()

#         response = self.client.get(self.url_get_current)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['markup'], self.default_pricing['markup'])
#         self.assertEqual(response.data['fee_usd'], self.default_pricing['fee_usd'])
#         self.assertEqual(response.data['fee_gbp'], self.default_pricing['fee_gbp'])
#         self.assertEqual(response.data['gps_ghs'], self.default_pricing['gbp_ghs'])
#         self.assertEqual(response.data['gbp_usd'], self.default_pricing['gbp_usd'])
#         self.assertEqual(response.data['gbp_sll'], self.default_pricing['gbp_sll'])
