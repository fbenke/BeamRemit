import random
import math

from django.db import models

from django.core.exceptions import ValidationError
from django.utils import timezone

from userena.utils import get_user_model

from pricing.models import Pricing, get_current_object


class Recipient(models.Model):

    first_name = models.CharField(
        'First Name',
        max_length=50,
        help_text='First name of recipient'
    )
    last_name = models.CharField(
        'Full Name',
        max_length=50,
        help_text='Last name of recipient'
    )
    phone_number = models.CharField(
        'Mobile Money Phone Number',
        max_length=15,
        help_text='Mobile Money Account of recipient'
    )

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Transaction(models.Model):

    class Meta:
        ordering = ['-initialized_at']

    # Constants
    INIT = 'INIT'
    PAID = 'PAID'
    INVALID = 'INVD'
    PROCESSED = 'PROC'
    CANCELLED = 'CANC'

    TRANSACTION_STATES = (
        (INIT, 'initialized'),
        (PAID, 'paid'),
        (CANCELLED, 'cancelled'),
        (PROCESSED, 'processed'),
        (INVALID, 'invalid')
    )

    recipient = models.ForeignKey(
        Recipient,
        related_name='transactions',
        help_text='Recipient associated with that transaction'
    )

    sender = models.ForeignKey(
        get_user_model(),
        related_name='transactions',
        help_text='Sender associated with that transaction'
    )

    pricing = models.ForeignKey(
        Pricing,
        related_name='transaction',
        help_text='Pricing information to enable conversion of btc to ghs'
    )

    amount_gbp = models.FloatField(
        'Remittance amount in GBP',
        help_text='Amount of GBP sent via Beam (does not include fees)'
    )

    amount_btc = models.FloatField(
        'Bitcoins paid to Beam',
        null=True,
        blank=True,
        help_text='BTCs equivalent of GBP amount, determined by Payment Processor'
    )

    amount_ghs = models.FloatField(
        'GHS payed out to recipient',
        help_text='GHS to be paid to recipient'
    )

    reference_number = models.CharField(
        'Reference Number',
        max_length=6,
        help_text='6-digit reference number given to the customer to refer to transaction in case of problems'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=TRANSACTION_STATES,
        default=INIT,
        help_text='State of the transaction. ' +
                  'Init - Payment initiated. ' +
                  'Paid - BTC with Beam. ' +
                  'Processed (manual) - Payout completed by Beam. ' +
                  'Invalid - Error communicated by payment processor.' +
                  'Cancelled (manual) - Cancelled by Beam, because we could not complete MM payout'
    )

    initialized_at = models.DateTimeField(
        'Initialized at',
        auto_now_add=True,
        help_text='Time at which transaction was created by sender'
    )
    paid_at = models.DateTimeField(
        'Paid at',
        null=True,
        blank=True,
        help_text='Time at which payment was confirmed with payment gateway'
    )
    processed_at = models.DateTimeField(
        'Processed at',
        null=True,
        blank=True,
        help_text='Time at which equivalent amount was sent to customer'
    )
    cancelled_at = models.DateTimeField(
        'Cancelled at',
        null=True,
        blank=True,
        help_text='Time at which the transaction was cancelled and rolled back'
    )
    invalidated_at = models.DateTimeField(
        'Invalidated at',
        null=True,
        blank=True,
        help_text='Time at which payment was set invalid'
    )

    comments = models.TextField(
        'Comments',
        blank=True,
        help_text='Leave comments when manually solving problems with this transaction'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.pricing = get_current_object(Pricing)
            self._generate_reference_number()
            self.amount_btc = self._calculate_ghs_price()
        else:
            original = Transaction.objects.get(pk=self.pk)
            if original.pricing != self.pricing:
                raise ValidationError('Pricing cannot be changed after initialization')

        super(Transaction, self).save(*args, **kwargs)

    def set_invalid(self, commit=True):
        self.state = Transaction.INVALID
        self.invalidated_at = timezone.now()
        if commit:
            self.save()

    def set_paid(self, commit=True):
        self.state = Transaction.PAID
        self.paid_at = timezone.now()
        if commit:
            self.save()

    def _generate_reference_number(self):
        self.reference_number = str(random.randint(10000, 999999))

    def _calculate_ghs_price(self):
        raw_price = self.amount_gbp * self.pricing.exchange_rate
        self.amount_ghs = math.ceil(raw_price * 10) / 10
