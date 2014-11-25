import random

from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

from django_countries.fields import CountryField

from beam.utils import mails

from pricing.models import Pricing, ExchangeRate


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
    PROCESSED = 'PROC'
    CANCELLED = 'CANC'
    INVALID = 'INVD'

    TRANSACTION_STATES = (
        (INIT, 'initialized'),
        (PAID, 'paid'),
        (PROCESSED, 'processed'),
        (CANCELLED, 'cancelled'),
        (INVALID, 'invalid')
    )

    SENT_CURRENCIES = (
        (settings.GBP, 'British Pound'),
        (settings.USD, 'US Dollar')
    )

    recipient = models.ForeignKey(
        Recipient,
        related_name='transactions',
        help_text='Recipient associated with that transaction'
    )

    sender = models.ForeignKey(
        User,
        related_name='transactions',
        help_text='Sender associated with that transaction'
    )

    pricing = models.ForeignKey(
        Pricing,
        related_name='transaction',
        help_text='Pricing information associated with that transaction'
    )

    exchange_rate = models.ForeignKey(
        ExchangeRate,
        related_name='transaction',
        help_text='Exchange Rates applied to this transaction'
    )

    sent_amount = models.FloatField(
        'Sent remittance amount',
        help_text='Amount sent via Beam (does not include fees)'
    )

    sent_currency = models.CharField(
        'Sent currency',
        max_length=4,
        choices=SENT_CURRENCIES,
        help_text='Currency the sent amount is denominated in'
    )

    amount_btc = models.FloatField(
        'Bitcoins paid to Beam',
        null=True,
        blank=True,
        help_text='BTC to be sent to Beam (before fees), determined by Payment Processor, exclusive BTC transaction fee'
    )

    received_amount = models.FloatField(
        'Remittance amount in received currency',
        help_text='Amount payed out to recipient in their currency'
    )

    receiving_country = CountryField(
        'Receiving Country',
        help_text='Country to which remittance is sent'
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

    @property
    def received_currency(self):
        return settings.COUNTRY_CURRENCY[self.receiving_country]

    @property
    def fee(self):
        return self.pricing.fee

    def __unicode__(self):
        return '{}'.format(self.id)

    def save(self, *args, **kwargs):
        if self.pk:
            original = Transaction.objects.get(pk=self.pk)
            if original.pricing != self.pricing:
                raise ValidationError('Pricing cannot be changed after initialization')
            if original.exchange_rate != self.exchange_rate:
                raise ValidationError('Exchange Rate cannot be changed after initialization')
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

    def generate_reference_number(self):
        self.reference_number = str(random.randint(10000, 999999))

    def post_paid(self):

        mails.send_mail(
            subject_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_SUBJECT,
            email_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_TEXT,
            context={
                'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                'protocol': settings.PROTOCOL,
                'id': self.id,
                'site_name': Site.objects.get_current().name
            },
            to_email=mails.get_admin_mail_addresses()
        )

        # Bitcoin Against Ebola Project Specifics
        if self.receiving_country == settings.SIERRA_LEONE and\
           self.recipient.phone_number not in settings.CHARITIES.values():

            mails.send_mail(
                subject_template_name=settings.SPLASH_ONBOARD_RECIPIENT_SUBJECT,
                email_template_name=settings.SPLASH_ONBOARD_RECIPIENT_TEXT,
                context={
                    'txn_id': self.id,
                    'timestamp': timezone.now(),
                    'amount_sll': self.received_amount,
                    'sender_first_name': self.sender.first_name,
                    'sender_last_name': self.sender.last_name,
                    'city': self.sender.profile.city,
                    'country': self.sender.profile.country,
                    'recipient_first_name': self.recipient.first_name,
                    'recipient_last_name': self.recipient.last_name,
                    'phone_number': self.recipient.phone_number,
                },
                to_email=settings.SPLASH_EMAIL
            )

    def post_paid_problem(self):

        mails.send_mail(
            subject_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_SUBJECT,
            email_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_TEXT,
            context={
                'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                'protocol': settings.PROTOCOL,
                'id': self.id,
                # TODO: decouple from specific payment provider
                'invoice_state': self.gocoin_invoice.state,
                'site_name': Site.objects.get_current().name
            },
            to_email=mails.get_admin_mail_addresses()
        )

    def post_processed(self):

        context = {
            'protocol': settings.PROTOCOL,
            'site': self.pricing.site,
            'first_name': self.sender.first_name,
            'sent_amount': self.sent_amount,
            'sent_currency': self.sent_currency,
            'received_amount': self.received_amount,
            'received_currency': self.received_currency,
            'mobile': self.recipient.phone_number,
            'txn_history': settings.MAIL_TRANSACTION_HISTORY_SITE
        }

        # charities for bitcoinagainstebola project have a slightly different email
        if self.receiving_country == settings.SIERRA_LEONE and\
           self.recipient.phone_number in settings.CHARITIES.values():

            context['recipient'] = self.recipient.last_name

            mails.send_mail(
                subject_template_name=settings.MAIL_TRANSACTION_COMPLETE_SUBJECT,
                email_template_name=settings.SPLASH_DONATION_COMPLETE_TEXT,
                html_email_template_name=settings.SPLASH_DONATION_COMPLETE_HTML,
                context=context,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=self.sender.email
            )

        else:
            context['recipient'] = self.recipient.first_name

            mails.send_mail(
                subject_template_name=settings.MAIL_TRANSACTION_COMPLETE_SUBJECT,
                email_template_name=settings.MAIL_TRANSACTION_COMPLETE_TEXT,
                context=context,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=self.sender.email,
                html_email_template_name=settings.MAIL_TRANSACTION_COMPLETE_HTML
            )
