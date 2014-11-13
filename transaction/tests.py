from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from userena.models import UserenaSignup

from beam.tests import TestUtils

from transaction import constants


class TransactionTests(APITestCase, TestUtils):
    plain_url_get_transaction = 'transaction:get'
    url_view_transactions = reverse('transaction:list')
    url_create_transaction = reverse('transaction:add')

    @classmethod
    def setUpClass(cls):
        UserenaSignup.objects.check_permissions()

    def tearDown(self):
        self.client.logout()


class GetTransaction(TransactionTests):

    def test_permissions(self):
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_admin_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_transaction(self):
        user = self._create_fully_verified_user()
        pricing = self._create_pricing()
        t = self._create_default_transaction(user, pricing)
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(t.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], t.id)
        self.assertEqual(response.data['recipient']['first_name'], t.recipient.first_name)
        self.assertEqual(response.data['recipient']['last_name'], t.recipient.last_name)
        self.assertEqual(response.data['recipient']['phone_number'], t.recipient.phone_number)
        self.assertEqual(response.data['sent_amount'], t.sent_amount)
        self.assertEqual(response.data['sent_currency'], t.sent_currency)
        self.assertEqual(response.data['received_amount'], t.received_amount)
        self.assertEqual(response.data['received_currency'], t.received_currency)
        self.assertEqual(response.data['reference_number'], t.reference_number)
        self.assertEqual(response.data['state'], t.state)
        self.assertEqual(response.data['paid_at'], t.paid_at)
        self.assertEqual(response.data['processed_at'], t.processed_at)
        self.assertEqual(response.data['initialized_at'], t.initialized_at)

    def test_get_transactions_not_found(self):
        user = self._create_fully_verified_user()
        pricing = self._create_pricing()
        transaction = self._create_default_transaction(user, pricing)
        another_user = self._create_fully_verified_user()
        token = self._create_token(another_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # try to get somebody else's transaction
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(transaction.id,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # try to get your own transaction
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1000,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ViewTransactions(TransactionTests):

    def test_permissions(self):
        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_admin_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_transactions(self):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        pricing = self._create_pricing()
        self._create_default_transaction(user, pricing)
        self._create_default_transaction(user, pricing)
        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.data['count'], 2)

        transaction = self._create_default_transaction(user, pricing)
        transaction.state = 'INIT'
        transaction.save()
        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.data['count'], 2)


class CreateTransaction(TransactionTests):

    def test_permissions(self):
        response = self.client.get(self.url_create_transaction)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_admin_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_create_transaction)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sending_currency_fail(self):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        pricing = self._create_pricing()

        data = {
            'pricing_id': pricing.id,
            'sent_amount': 500,
            'sent_currency': 'EUR',
            'receiving_country': 'USA',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Select a valid choice.' in response.data['sent_currency'][0])
        self.assertTrue('Select a valid choice.', response.data['receiving_country'][0])

    def test_pricing_expired(self):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_pricing()
        pricing = self._create_pricing()

        data = {
            'pricing_id': pricing.id - 1,
            'sent_amount': 500,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.PRICING_EXPIRED)

    def test_profile_incomplete(self):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        pricing = self._create_pricing()

        data = {
            'pricing_id': pricing.id,
            'sent_amount': 500,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.PROFILE_INCOMPLETE)
