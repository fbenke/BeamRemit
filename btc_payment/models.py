from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db import transaction as dbtransaction
from django.utils.timezone import utc

from transaction.models import Transaction

from beam.utils.log import log_error
from beam.utils.security import generate_signature
from beam.utils.exceptions import APIException

from btc_payment.api_calls import gocoin, blockchain
from btc_payment.api_calls.coinapult import CoinapultClient, CoinapultError

from datetime import timedelta, datetime


class DummyInvoice(object):

    @staticmethod
    def initiate(transaction):
        return {}


class GoCoinInvoice(models.Model):

    UNPAID = 'UNPD'
    PAID = 'PAID'
    UNDERPAID = 'UNDP'
    READY_TO_SHIP = 'SHIP'
    INVALID = 'INVD'
    MERCHANT_REVIEW = 'MRCH'

    INVOICE_STATES = (
        (UNPAID, 'unpaid'),
        (PAID, 'paid'),
        (UNDERPAID, 'underpaid'),
        (READY_TO_SHIP, 'ready to ship'),
        (INVALID, 'invalid'),
        (MERCHANT_REVIEW, 'manual handling required')
    )

    transaction = models.OneToOneField(
        Transaction,
        related_name='gocoin_invoice',
        help_text='Transaction associated with this payment'
    )

    invoice_id = models.CharField(
        'Invoice ID',
        max_length=36,
        help_text='UUID identifying generated invoice'
    )

    btc_address = models.CharField(
        'BTC Wallet Address',
        max_length=34,
        help_text='Wallet generated to receive this payment'
    )

    btc_usd = models.FloatField(
        'BTC to USD Exchange Rate',
        null=True,
        help_text='exchange rate from BTC to USD applied for this payment'
    )

    sender_usd = models.FloatField(
        'Sender Currency to USD Exchange Rate',
        null=True,
        help_text='exchange rate from sender currency to USD applied for this payment'
    )

    balance_due = models.FloatField(
        'Balance Due',
        null=True,
        help_text='GoCoin allows several BTC payments for one item, which are added up. Negative balance means "overpaid"'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=INVOICE_STATES,
        default=UNPAID,
        help_text='State of the Coinbase Invoice'
    )

    @staticmethod
    def initiate(transaction):
        message = (str(transaction.id) + str(transaction.sent_amount + transaction.fee.amount) +
                   settings.GOCOIN_INVOICE_CALLBACK_URL)

        signature = generate_signature(message, settings.GOCOIN_API_KEY)

        redirect_url = settings.GOCOIN_PAYMENT_REDIRECT[transaction.pricing.site.id].format(transaction.id)

        result = gocoin.generate_invoice(
            price=transaction.sent_amount + transaction.fee.amount,
            reference_number=transaction.reference_number,
            transaction_id=transaction.id,
            signature=signature,
            currency=transaction.sent_currency,
            redirect_url=redirect_url
        )

        try:
            gocoin_invoice = GoCoinInvoice(
                transaction=transaction,
                invoice_id=result['id'],
                btc_address=result['payment_address'],
                btc_usd=result['inverse_spot_rate'],
                sender_usd=result['usd_spot_rate']
            )

            transaction.amount_btc = result['price']

            with dbtransaction.atomic():
                gocoin_invoice.save()
                transaction.gocoin_invoice = GoCoinInvoice.objects.get(id=gocoin_invoice.id)
                transaction.save()

            return {'invoice_id': gocoin_invoice.invoice_id}

        except KeyError as e:
            message = 'ERROR - GoCoin Create Invoice: received invalid response, {}, {}'
            log_error(message.format(e, result))
            raise APIException


class BlockchainInvoice(models.Model):

    UNPAID = 'UNPD'
    PAID = 'PAID'
    UNDERPAID = 'UNDP'
    READY_TO_SHIP = 'SHIP'
    MERCHANT_REVIEW = 'MRCH'

    INVOICE_STATES = (
        (UNPAID, 'unpaid'),
        (PAID, 'paid'),
        (UNDERPAID, 'underpaid'),
        (READY_TO_SHIP, 'ready to ship'),
        (MERCHANT_REVIEW, 'manual handling required')
    )

    transaction = models.OneToOneField(
        Transaction,
        related_name='blockchain_invoice',
        help_text='Transaction associated with this payment'
    )

    created_at = models.DateTimeField(
        'Created at',
        auto_now_add=True,
        help_text='Time at which this invoice was created, needed to determine timeframe within payments are accepted'
    )

    btc_address = models.CharField(
        'BTC Wallet Address',
        max_length=34,
        help_text='Wallet generated to receive this payment'
    )

    invoice_id = models.CharField(
        'Invoice ID',
        max_length=36,
        help_text='UUID identifying generated invoice'
    )

    btc_usd = models.FloatField(
        'BTC to USD Exchange Rate',
        null=True,
        help_text='exchange rate from BTC to USD applied for this payment'
    )

    sender_usd = models.FloatField(
        'Sender Currency to USD Exchange Rate',
        null=True,
        help_text='exchange rate from sender currency to USD applied for this payment'
    )

    balance_due = models.FloatField(
        'Balance Due',
        null=True,
        help_text='Several BTC payments for one item are possible. Negative balance means "overpaid"'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=INVOICE_STATES,
        default=UNPAID,
        help_text='State of the Invoice'
    )

    @property
    def expires_at(self):
        return self.created_at + timedelta(minutes=settings.BLOCKCHAIN_INVOICE_TIMEOUT)

    @staticmethod
    def initiate(transaction):

        invoice_id = uuid4()

        btc_address = blockchain.generate_receiving_address(
            invoice_id=invoice_id, transaction_id=transaction.id
        )

        transaction_value = transaction.sent_amount + transaction.fee.amount

        amount_btc, btc_usd, sender_usd = blockchain.convert_to_btc(
            amount=transaction_value,
            currency=transaction.sent_currency
        )

        blockchain_invoice = BlockchainInvoice(
            transaction=transaction,
            btc_address=btc_address,
            invoice_id=invoice_id,
            btc_usd=btc_usd,
            sender_usd=sender_usd,
            balance_due=amount_btc
        )

        transaction.amount_btc = amount_btc

        with dbtransaction.atomic():
            blockchain_invoice.save()
            transaction.blockchain_invoice = BlockchainInvoice.objects.get(id=blockchain_invoice.id)
            transaction.save()

        return {
            'amount_btc': amount_btc,
            'btc_address': btc_address,
            'expires': blockchain_invoice.expires_at
        }

    def update(self, payment):

       # handle notifications sent late
        if payment.received_at > self.expires_at:
            self.state = self.MERCHANT_REVIEW
            self.transaction.set_invalid()
            self.transaction.post_paid_problem()
        else:
            self.balance_due = self.balance_due - payment.amount
            if self.balance_due <= 0:
                self.state = self.PAID
                self.transaction.set_paid()
                self.transaction.post_paid()
            else:
                self.state = self.UNDERPAID

        self.save()

    def confirm(self):
        if self.balance_due > 0:
            return
        for p in self.payments.all():
            if p.state == BlockchainPayment.PENDING:
                return
        self.state = self.READY_TO_SHIP
        self.save()


class BlockchainPayment(models.Model):

    PENDING = 'PEND'
    CONFIRMED = 'CONF'

    PAYMENT_STATES = (
        (PENDING, 'pending'),
        (CONFIRMED, 'confirmed')
    )

    invoice = models.ForeignKey(
        BlockchainInvoice,
        related_name='payments',
        help_text='Invoice associated with that transaction'
    )

    input_transaction_hash = models.CharField(
        'Input Transaction Hash',
        max_length=64,
        help_text='Hash of the payment transaction'
    )

    forward_transaction_hash = models.CharField(
        'ForwardTransaction Hash',
        max_length=64,
        help_text='Hash of the transaction forwarding the payment to Beam\'s receiving address'
    )

    amount = models.FloatField(
        'Amount',
        null=True,
        help_text='Amount in BTC'
    )

    received_at = models.DateTimeField(
        'Received at',
        auto_now_add=True,
        help_text='Time at which callback for this payment was received'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=PAYMENT_STATES,
        default=PENDING,
        help_text='State of the Invoice'
    )


class CoinapultInvoice(models.Model):

    UNPAID = 'UNPD'
    PAID = 'PAID'
    READY_TO_SHIP = 'SHIP'
    MERCHANT_REVIEW = 'MRCH'
    EXPIRED = 'EXPD'

    INVOICE_STATES = (
        (UNPAID, 'unpaid'),  # this equals coinapult status "pending"
        (PAID, 'paid'),  # this equals coinapult status "confirming"
        (READY_TO_SHIP, 'ready to ship'),  # this equals coinapult status "complete"
        (EXPIRED, 'expired'),  # this equals coinapult status "cancelled"
        (MERCHANT_REVIEW, 'manual handling required'),  # this equals coinapult status "cancelled" with errors
    )

    transaction = models.OneToOneField(
        Transaction,
        related_name='coinapult_invoice',
        help_text='Transaction associated with this invoice'
    )

    expires_at = models.DateTimeField(
        'Expires at',
        help_text='Time at which this invoice expires'
    )

    completed_at = models.DateTimeField(
        'Completed at',
        null=True,
        help_text='Time at which this invoice was completed'
    )

    btc_address = models.CharField(
        'BTC Address',
        max_length=34,
        help_text='BTC Address generated to receive this payment'
    )

    invoice_id = models.CharField(
        'Invoice ID',
        max_length=36,
        help_text='UUID identifying generated invoice'
    )

    btc_fiat = models.FloatField(
        'BTC to Sending Currency',
        null=True,
        help_text='exchange rate from BTC to sending currency applied for this payment'
    )

    balance_due = models.FloatField(
        'Balance Due',
        null=True,
        help_text='Several BTC payments for one item are possible. Negative balance means "overpaid"'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=INVOICE_STATES,
        default=UNPAID,
        help_text='State of the Invoice'
    )

    @property
    def created_at(self):
        return self.expires_at - timedelta(minutes=settings.COINAPULT_INVOICE_TIMEOUT)

    @staticmethod
    def initiate(transaction):

        try:

            client = CoinapultClient(
                baseURL=settings.COINAPULT_API_BASE_URL,
                credentials={'key': settings.COINAPULT_API_KEY, 'secret': settings.COINAPULT_API_SECRET},
                authmethod='cred'
            )

            transaction_value = transaction.sent_amount + transaction.fee.amount

            resp = client.lock(
                amount=0,
                outAmount=transaction_value,
                currency=transaction.sent_currency,
                callback=settings.COINAPULT_INVOICE_CALLBACK_URL
            )

            # resp = client.receive(outAmount=transaction_value, outCurrency='USD')

            coinapult_invoice = CoinapultInvoice(
                transaction=transaction,
                expires_at=datetime.fromtimestamp((resp['expiration'])).replace(tzinfo=utc),
                btc_address=resp['address'],
                invoice_id=resp['transaction_id'],
                btc_fiat=float(resp['quote']['bid']),
                balance_due=float(resp['in']['expected'])
            )

            transaction.amount_btc = float(resp['in']['expected'])

            with dbtransaction.atomic():
                coinapult_invoice.save()
                transaction.coinapult_invoice = CoinapultInvoice.objects.get(id=coinapult_invoice.id)
                transaction.save()

            return {
                'invoice_id': coinapult_invoice.invoice_id,
                'invoice_url': settings.COINAPULT_INVOICE_URL.format(coinapult_invoice.invoice_id)
            }

        except CoinapultError as e:
            message = 'ERROR - Coinapult Create Invoice: {}, Txn id: {}'
            log_error(message.format(e, transaction.id))

        except KeyError as e:
            message = 'ERROR - Coinapult Create Invoice: received invalid response, {}, {}'
            log_error(message.format(e, resp))

        except APIException as e:
            message = 'ERROR - Coinapult Create Invoice: failed to send request, {}'
            log_error(message.format(e))

        raise APIException
