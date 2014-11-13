from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from userena.models import UserenaSignup


class TransactionTests(APITestCase, TestUtils):
    plain_url_get_transaction = 'transaction:get'


class GetTransaction(TransactionTests):

    def setUp(self):
        UserenaSignup.objects.check_permissions()
        self.user = self._create_fully_verified_user()
        self.pricing = self._create_pricing()
        self.transaction = self._create_default_transaction(self.user, self.pricing)

    def test_permissions(self):
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1,)))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_admin_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_transaction(self):
        token = self._create_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(self.transaction.id,)))
        t = self.transaction
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
        another_user = self._create_fully_verified_user()
        token = self._create_token(another_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        # try to get somebody else's transaction
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(self.transaction.id,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # try to get your own transaction
        response = self.client.get(reverse(self.plain_url_get_transaction, args=(1000,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
