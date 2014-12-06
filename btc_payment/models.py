from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db import transaction as dbtransaction

from transaction.models import Transaction

from beam.utils.log import log_error
from beam.utils.security import generate_signature

from btc_payment.api_calls import gocoin, blockchain

from datetime import timedelta


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
        message = (str(transaction.id) + str(transaction.sent_amount + transaction.fee) +
                   settings.GOCOIN_INVOICE_CALLBACK_URL)

        signature = generate_signature(message, settings.GOCOIN_API_KEY)

        redirect_url = settings.GOCOIN_PAYMENT_REDIRECT[transaction.receiving_country].format(transaction.id)

        result = gocoin.generate_invoice(
            price=transaction.sent_amount + transaction.fee,
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


class BlockchainInvoice(models.Model):

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
        return self.created_at + timedelta(minutes=settings.BLOCKCHAIN_TIMEOUT)

    @staticmethod
    def initiate(transaction):

        invoice_id = uuid4()

        btc_address = blockchain.generate_receiving_address(
            invoice_id=invoice_id,
        )

        transaction_value = transaction.sent_amount + transaction.fee

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
        else:
            self.balance_due = self.balance_due - payment.amount
            if self.balance_due <= 0:
                self.state = self.PAID
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
