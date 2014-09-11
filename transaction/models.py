from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from userena.utils import get_user_model

from beam.utils import log_error


class Pricing(models.Model):

    start = models.DateTimeField(
        'Start Time',
        auto_now_add=True,
        help_text='Time at which pricing structure came into effect'
    )

    end = models.DateTimeField(
        'End Time',
        blank=True,
        null=True,
        help_text='Time at which pricing ended. If null, it represents the current pricing structure. ' +
                  'Only one row in this table can have a null value for this column.'
    )

    markup = models.FloatField(
        'Markup',
        help_text='Percentage to be added over exchange rate. Value between 0 and 1.'
    )

    ghs_usd = models.FloatField(
        'GHS/USD Exchange Rate',
        help_text='Amount of GHS you get for 1 USD'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    @staticmethod
    def get_current_pricing():
        return Pricing.objects.get(end__isnull=True)

    @staticmethod
    def end_previous_pricing():
        try:
            previous_pricing = Pricing.objects.get(end__isnull=True)
            previous_pricing.end = timezone.now()
            previous_pricing.save()
        except ObjectDoesNotExist:
            log_error('ERROR - Failed to end previous pricing.')


class Recipient(models.Model):
    name = models.CharField(
        'Full Name',
        max_length=50,
        help_text='Full name of recipient'
    )
    phone_number = models.CharField(
        'Mobile Money Phone Number',
        max_length=15,
        help_text='Mobile Money Account of recipient'
    )
    notification_email = models.EmailField(
        'Email Address',
        blank=True,
        help_text='Email Address of recipient'
    )


class Transaction(models.Model):

    class Meta:
        ordering = ['-initialized_at']

    # Constants
    INIT = 'INIT'
    PAID = 'PAID'
    PROCESSED = 'PROC'
    DECLINED = 'DECL'
    CANCELLED = 'CANC'

    TRANSACTION_STATUS = (
        (INIT, 'initialized'),
        (PAID, 'paid'),
        (CANCELLED, 'cancelled'),
        (DECLINED, 'declined'),
        (PROCESSED, 'processed'),
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
        related_name='transactions',
        help_text='Pricing information to enable conversion of btc to ghs'
    )

    amount_btc = models.IntegerField(
        'Satoshi received',
        # null=True,
        # blank=True,
        help_text='BTCs transferred by sender'
    )

    amount_ghs = models.FloatField(
        'GHS payed out to recipient',
        # null=True,
        help_text='GHS to be paid to Kitiwa'
    )

    reference_number = models.CharField(
        'Reference Number',
        max_length=6,
        help_text='6-digit reference number given to the customer to refer to transaction in case of problems'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=TRANSACTION_STATUS,
        default=INIT,
        help_text='State of the transaction'
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
    declined_at = models.DateTimeField(
        'Declined at',
        null=True,
        blank=True,
        help_text='Time at which the transaction was declined by payment gateway'
    )
    cancelled_at = models.DateTimeField(
        'Cancelled at',
        null=True,
        blank=True,
        help_text='Time at which the transaction was cancelled and rolled back'
    )

    def set_invalid(self):
        self.state = Transaction.INVALID
        self.declined_at = timezone.now()
        self.save()

    def set_declined(self):
        self.state = Transaction.DECLINED
        self.declined_at = timezone.now()
        self.save()

    def set_paid(self):
        self.state = Transaction.PAID
        self.paid_at = timezone.now()
        self.save()
