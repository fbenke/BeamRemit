from django.conf import settings
from django.db import models
from django.db import transaction as dbtransaction

from transaction.models import Transaction

from beam.utils.security import generate_signature

from btc_payment.api_calls import gocoin


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

        redirect_url = settings.PROTOCOL + '://' + settings.COUNTRY_SITE[transaction.receiving_country] +\
            settings.GOCOIN_INVOICE_REDIRECT_SUFFIX.format(transaction.id)

        result = gocoin.generate_invoice(
            price=transaction.sent_amount + transaction.fee,
            reference_number=transaction.reference_number,
            transaction_id=transaction.id,
            signature=signature,
            currency=transaction.sent_currency,
            redirect_url=redirect_url
        )

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

        return gocoin_invoice.invoice_id
