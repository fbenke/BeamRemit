from django.core.urlresolvers import reverse

from rest_framework import status

from beam.tests import BeamAPITestCase


class PricingTests(BeamAPITestCase):

    url_add = reverse('pricing:add')
    url_get_current = reverse('pricing:current')
    plain_url_get_detail = 'pricing:detail'

    def test_add(self):
        token, _ = self._create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_add, {'markup': 0.3, 'ghs_usd': 3.54})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_fail(self):
        token, _ = self._create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_add, {'markup': 1.3, 'ghs_usd': 3.54})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['markup'][0], 'markup has to be a value between 0 and 1')

    def test_get_current(self):
        token, _ = self._create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post(self.url_add, {'markup': 0.3, 'ghs_usd': 3.54})

        response = self.client.get(self.url_get_current)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['markup'], 0.3)
        self.assertEqual(response.data['ghs_usd'], 3.54)

        response = self.client.post(self.url_add, {'markup': 0.6, 'ghs_usd': 4})

        response = self.client.get(self.url_get_current)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['markup'], 0.6)
        self.assertEqual(response.data['ghs_usd'], 4)

    def test_get_detail(self):
        token, _ = self._create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        ids = []

        for i in xrange(1, 5):
            response = self.client.post(self.url_add, {'markup': float(i) / 10, 'ghs_usd': i})
            ids.append(response.data['id'])

        for i in xrange(1, 5):
            response = self.client.get(reverse(self.plain_url_get_detail, args=(ids[i - 1],)))
            self.assertEqual(response.data['markup'], float(i) / 10)
            self.assertEqual(response.data['ghs_usd'], i)

    def test_get_detail_fail(self):
        token, _ = self._create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.post(self.url_add, {'markup': 0.1, 'ghs_usd': 1})
        id = response.data['id']
        response = self.client.get(reverse(self.plain_url_get_detail, args=(id + 1,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Not found')
