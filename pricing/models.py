import math
import collections

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

from jsonfield import JSONField

from beam.utils.log import log_error


def get_current_object(cls):
    try:
        return cls.objects.get(end__isnull=True)
    except ObjectDoesNotExist:
        log_error('ERROR {} - No pricing object found.'.format(cls))
        raise ObjectDoesNotExist


def end_previous_object(cls):
    try:
        previous_object = cls.objects.get(end__isnull=True)
        previous_object.end = timezone.now()
        previous_object.save()
    except ObjectDoesNotExist:
        if cls.objects.all().exists():
            log_error('ERROR {} - Failed to end previous pricing.'.format(cls))


def get_current_object_by_site(cls, site):
    try:
        return cls.objects.get(end__isnull=True, site=site)
    except ObjectDoesNotExist:
        log_error('ERROR {} - No pricing object found.'.format(cls))
        raise ObjectDoesNotExist


def end_previous_object_by_site(cls, site):
    try:
        previous_object = cls.objects.get(end__isnull=True, site=site)
        previous_object.end = timezone.now()
        previous_object.save()
    except ObjectDoesNotExist:
        if cls.objects.all().exists():
            log_error('ERROR {} - Failed to end previous pricing.'.format(cls))


class Pricing(models.Model):

    # TODO: which constants can go away?
    COUNTRY_FXR = {
        settings.GHANA: 'exchange_rate_ghs',
        settings.SIERRA_LEONE: 'exchange_rate_sll'
    }

    FEE_CURRENCIES = (
        (settings.GBP, 'British Pound'),
        (settings.USD, 'US Dollar')
    )

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

    fee = models.FloatField(
        'Fixed Fee',
        help_text='Fixed Fee charged for the money transfer.'
    )

    fee_currency = models.CharField(
        'Fee currency',
        max_length=4,
        choices=FEE_CURRENCIES,
        help_text='Currency the fee is denominated in.'
    )

    site = models.ForeignKey(
        Site,
        related_name='pricing',
        help_text='Site associated with this pricing'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    @property
    def exchange_rate_ghs(self):
        return get_current_object(ExchangeRate).gbp_ghs * (1 - self.markup)

    @property
    def exchange_rate_sll(self):
        return get_current_object(ExchangeRate).gbp_sll * (1 - self.markup)

    def calculate_received_amount(self, sent_amount, currency, country):

        # if necessary, convert the sent amount into the base currency, no markup included
        amount_gbp = get_current_object(ExchangeRate).convert_to_base_currency(sent_amount, currency)

        # convert from base currency to received currency, this includes the markup
        undrounded_amount = amount_gbp * getattr(self, self.COUNTRY_FXR[country])

        # do country-specific rounding
        if country == settings.SIERRA_LEONE:
            return math.ceil(undrounded_amount / 10) * 10
        else:
            return math.ceil(undrounded_amount * 10) / 10


class ExchangeRate(models.Model):

    SENT_CURRENCY_FXR = {
        settings.USD: 'gbp_usd'
    }

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

    gbp_ghs = models.FloatField(
        'GBP to GHS Exchange Rate',
        help_text='Exchange Rate from GBP to GHS without markup'
    )

    gbp_usd = models.FloatField(
        'GBP to USD Exchange Rate',
        help_text='Exchange Rate from GBP to USD without markup'
    )

    gbp_sll = models.FloatField(
        'GBP to SSL Exchange Rate',
        help_text='Exchange Rate from GBP to SSL without markup'
    )

    def convert_to_base_currency(self, amount, currency):
        if currency != settings.GBP:
            return amount / getattr(self, self.SENT_CURRENCY_FXR[currency])
        else:
            return amount


class Comparison(models.Model):

    price_comparison = JSONField(
        'Price Comparison',
        load_kwargs={'object_pairs_hook': collections.OrderedDict},
        help_text='JSON description of selected competitor\'s pricing structure'
    )

    start = models.DateTimeField(
        'Start Time',
        auto_now_add=True,
        help_text='Time at which the prices were retrieved'
    )

    end = models.DateTimeField(
        'End Time',
        blank=True,
        null=True,
        help_text='Time at which comparison ended. If null, it represents the current comparison. ' +
                  'Only one row in this table can have a null value for this column.'
    )


class Limit(models.Model):

    def __init__(self, *args, **kwargs):
        super(Limit, self).__init__(*args, **kwargs)
        try:
            pricing = get_current_object_by_site(Pricing, self.site)
            exchange_rate = get_current_object(ExchangeRate)
            self.exchange_rate_sll = pricing.exchange_rate_sll
            self.exchange_rate_ghs = pricing.exchange_rate_ghs
            self.transaction_min_gbp = exchange_rate.convert_to_base_currency(self.transaction_min, self.currency)
            self.transaction_max_gbp = exchange_rate.convert_to_base_currency(self.transaction_max, self.currency)
        except ObjectDoesNotExist:
            self.transaction_min_gbp = self.transaction_max_gbp = 0
            self.exchange_rate_sll = self.exchange_rate_ghs = 0

    LIMIT_CURRENCIES = (
        (settings.GBP, 'British Pound'),
        (settings.USD, 'US Dollar')
    )

    transaction_min = models.FloatField(
        'Minimum amount',
        help_text='Minimum remittance amount per transaction'
    )

    transaction_max = models.FloatField(
        'Maximum amount',
        help_text='Maximum remittance amount per transaction'
    )

    user_limit_basic = models.FloatField(
        'Maximum for basic users',
        help_text='Maximum amount a basic user is allowed to send per day'
    )

    user_limit_complete = models.FloatField(
        'Maximum for fully verified users',
        help_text='Maximum amount a fully verfied user is allowed to send per day'
    )

    currency = models.CharField(
        'Currency',
        max_length=4,
        choices=LIMIT_CURRENCIES,
        help_text='Currency the limits are denominated in.'
    )

    site = models.ForeignKey(
        Site,
        related_name='limit',
        help_text='Site associated with this limit'
    )

    start = models.DateTimeField(
        'Start Time',
        auto_now_add=True,
        help_text='Time at which limit became effective'
    )

    end = models.DateTimeField(
        'End Time',
        blank=True,
        null=True,
        help_text='Time at which limit was replaced. If null, it represents the current limit. ' +
                  'Only one row in this table can have a null value for this column.'
    )

    @property
    def transaction_min_sll(self):
        return self.transaction_min_gbp * self.exchange_rate_sll

    @property
    def transaction_max_sll(self):
        return self.transaction_max_gbp * self.exchange_rate_sll

    @property
    def transaction_min_ghs(self):
        return self.transaction_min_gbp * self.exchange_rate_ghs

    @property
    def transaction_max_ghs(self):
        return self.transaction_max_gbp * self.exchange_rate_ghs
