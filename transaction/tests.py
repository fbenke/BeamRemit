from django.core import mail as mailbox
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from userena.models import UserenaSignup

from beam.tests import TestUtils

from transaction import constants
from transaction.models import Transaction

from mock import patch

# from unittest import skip


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
        t = self._create_default_transaction(user)
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
        transaction = self._create_default_transaction(user)
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

        self._create_default_transaction(user)
        self._create_default_transaction(user)
        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.data['count'], 2)

        transaction = self._create_default_transaction(user)
        transaction.state = 'INIT'
        transaction.save()
        response = self.client.get(self.url_view_transactions)
        self.assertEqual(response.data['count'], 2)


class CreateTransaction(TransactionTests):

    @patch('transaction.views.CreateTransaction.post_save')
    def test_permissions(self, mock_transaction):
        response = self.client.get(self.url_create_transaction)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_admin_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.get(self.url_create_transaction, {}, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_sending_currency_fail(self, mock_transaction):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 500,
            'sent_currency': 'EUR',
            'receiving_country': 'USA',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Select a valid choice.' in response.data['sent_currency'][0])
        self.assertTrue('Select a valid choice.', response.data['receiving_country'][0])

    @patch('transaction.views.CreateTransaction.post_save')
    def test_site_curency_mismatch(self, mock_transaction):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 500,
            'sent_currency': 'USD',
            'receiving_country': 'SLL',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data['sent_currency'][0], constants.SENT_CURRENCY_NOT_SUPPORTED)
        self.assertTrue(response.data['receiving_country'][0], constants.COUNTRY_NOT_SUPPORTED)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_pricing_expired(self, mock_transaction):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_default_pricing_beam()
        pricing = self._create_default_pricing_beam()
        self._create_default_exchange_rate()
        exchange_rate = self._create_default_exchange_rate()

        data = {
            'pricing_id': pricing.id - 1,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 500,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.PRICING_EXPIRED)

        data['pricing_id'] = pricing.id
        data['exchange_rate_id'] = exchange_rate.id - 1
        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.PRICING_EXPIRED)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_profile_incomplete(self, mock_transaction):
        user = self._create_activated_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 500,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }
        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.PROFILE_INCOMPLETE)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_transaction_full_verification_required(self, mock_transaction):
        user = self._create_user_with_profile()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_default_limit_beam()
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        self._create_transaction(
            sender=user,
            pricing=pricing,
            exchange_rate=exchange_rate,
            sent_amount=40,
            sent_currency='GBP',
            received_amount=265,
            receiving_country='GH'
        )

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 10,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }

        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.ADDITIONAL_DOCUMENTS_MISSING)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_transaction_documents_pending(self, mock_transaction):
        user = self._create_user_with_uploaded_documents()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_default_limit_beam()
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        self._create_transaction(
            sender=user,
            pricing=pricing,
            exchange_rate=exchange_rate,
            sent_amount=40,
            sent_currency='GBP',
            received_amount=265,
            receiving_country='GH'
        )

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 10,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }

        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.DOCUMENTS_NOT_VERIFIED)

    @patch('transaction.views.CreateTransaction.post_save')
    def test_transaction_max_exceeded(self, mock_transaction):
        user = self._create_fully_verified_user()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_default_limit_beam()
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        self._create_transaction(
            sender=user,
            pricing=pricing,
            exchange_rate=exchange_rate,
            sent_amount=1000,
            sent_currency='GBP',
            received_amount=5300,
            receiving_country='GH'
        )

        data = {
            'pricing_id': pricing.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 10,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }

        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], constants.TRANSACTION_LIMIT_EXCEEDED)

    @patch('transaction.views.payment_class.initiate')
    def test_transaction_create_success(self, mock_payment_initiation):
        user = self._create_user_with_profile()
        token = self._create_token(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self._create_default_limit_beam()
        self._create_state(site_id=0)
        self._create_state(site_id=1)
        pricing_beam = self._create_default_pricing_beam()
        pricing_bae = self._create_default_pricing_bae()
        exchange_rate = self._create_default_exchange_rate()
        mock_payment_initiation.return_value = {'invoice_id': '12345'}

        data = {
            'pricing_id': pricing_beam.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 10,
            'sent_currency': 'GBP',
            'receiving_country': 'GH',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }

        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.beamremit.com/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invoice_id'], '12345')
        self.assertEqual(response.data['received_amount'], 51.5)
        self.assertEqual(response.data['received_currency'], 'GHS')
        self.assertEqual(response.data['operation_mode'], 'UP')

        mock_payment_initiation.return_value = {'invoice_id': '67890'}

        data = {
            'pricing_id': pricing_bae.id,
            'exchange_rate_id': exchange_rate.id,
            'sent_amount': 17,
            'sent_currency': 'USD',
            'receiving_country': 'SL',
            'recipient': {
                'first_name': 'Nikunj',
                'last_name': 'Handa',
                'phone_number': '0509392087'
            }
        }

        response = self.client.post(self.url_create_transaction, data, HTTP_REFERER='http://dev.bitcoinagainstebola.org/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invoice_id'], '67890')
        self.assertEqual(response.data['received_amount'], 74060)
        self.assertEqual(response.data['received_currency'], 'SLL')
        self.assertEqual(response.data['operation_mode'], 'UP')


class AdminTests(TestCase, TestUtils):

    @classmethod
    def setUpClass(cls):
        UserenaSignup.objects.check_permissions()

    def setUp(self):
        admin = self._create_admin_user(self.emails.next())
        self.client.login(username=admin.username, password=self.default_password)

    def test_cancel_transaction(self):
        user = self._create_user_with_profile()
        transaction = self._create_default_transaction(user)

        data = {
            'state': 'CANC',
            'comments': '',
            '_continue': 'Save and continue editing'
        }

        response = self.client.post(reverse(
            'admin:transaction_transaction_change',
            args=(transaction.id,)), data
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(transaction.state, 'CANC')

    def test_comment_transaction(self):
        user = self._create_user_with_profile()
        transaction = self._create_default_transaction(user)

        data = {
            'state': 'INIT',
            'comments': 'Left a comment',
            '_continue': 'Save and continue editing'
        }

        response = self.client.post(reverse(
            'admin:transaction_transaction_change',
            args=(transaction.id,)), data
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(transaction.comments, 'Left a comment')

    def test_process_transaction(self):
        no_emails = len(mailbox.outbox)
        user = self._create_user_with_profile()
        transaction = self._create_default_transaction(user)

        data = {
            'state': 'PROC',
            'comments': '',
            '_continue': 'Save and continue editing'
        }

        response = self.client.post(reverse(
            'admin:transaction_transaction_change',
            args=(transaction.id,)), data
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(transaction.state, 'PROC')
        self.assertEqual(len(mailbox.outbox), no_emails + 1)

    def test_process_transaction_bae(self):
        no_emails = len(mailbox.outbox)
        user = self._create_user_with_profile()
        pricing = self._create_default_pricing_beam()
        exchange_rate = self._create_default_exchange_rate()

        transaction = self._create_transaction(
            sender=user,
            pricing=pricing,
            exchange_rate=exchange_rate,
            sent_amount=10,
            sent_currency='USD',
            received_amount=29880,
            receiving_country='SL'
        )

        transaction.recipient.phone_number = '5275'
        transaction.recipient.save()

        data = {
            'state': 'PROC',
            'comments': '',
            '_continue': 'Save and continue editing'
        }

        response = self.client.post(reverse(
            'admin:transaction_transaction_change',
            args=(transaction.id,)), data
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(transaction.state, 'PROC')
        self.assertEqual(len(mailbox.outbox), no_emails + 1)
