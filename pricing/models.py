import math
import collections

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
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


class Pricing(models.Model):

    COUNTRY_FXR = {
        settings.GHANA: 'exchange_rate_ghs',
        settings.SIERRA_LEONE: 'exchange_rate_sll'
    }

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

    markup = models.FloatField(
        'Markup',
        help_text='Percentage to be added over exchange rate. Value between 0 and 1.'
    )

    fee_usd = models.FloatField(
        'Fixed Fee in USD',
        help_text='Fixed Fee charged for the money transfer in USD.'
    )

    fee_gbp = models.FloatField(
        'Fixed Fee in GBP',
        help_text='Fixed Fee charged for the money transfer in GBP.'
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

    def __unicode__(self):
        return '{}'.format(self.id)

    @property
    def exchange_rate_ghs(self):
        return self.gbp_ghs * (1 - self.markup)

    @property
    def exchange_rate_usd(self):
        return self.gbp_usd * (1 - self.markup)

    @property
    def exchange_rate_sll(self):
        return self.gbp_sll * (1 - self.markup)

    def calculate_received_amount(self, sent_amount, currency, country):

        # if necessary, convert the sent amount into the base currency
        if currency != settings.GBP:
            amount_gbp = sent_amount / getattr(self, self.SENT_CURRENCY_FXR[currency])
        else:
            amount_gbp = sent_amount

        print amount_gbp
        # convert from base currency to received currency
        undrounded_amount = amount_gbp * getattr(self, self.COUNTRY_FXR[country])

        print undrounded_amount
        # do country-specific rounding
        if country == settings.SIERRA_LEONE:
            return math.ceil(undrounded_amount / 10) * 10
        else:
            return math.ceil(undrounded_amount * 10) / 10


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
        current_object = get_current_object(Pricing)
        self.exchange_rate_ghs = current_object.gbp_ghs * (1 - current_object.markup)
        self.exchange_rate_sll = current_object.gbp_sll * (1 - current_object.markup)
        self.exchange_rate_usd = current_object.gbp_usd * (1 - current_object.markup)

    transaction_min_gbp = models.FloatField(
        'Minimum amount in GBP ',
        help_text='Minimum remittance amount in GBB per transaction'
    )

    transaction_max_gbp = models.FloatField(
        'Maximum amount in GBP ',
        help_text='Maximum remittance amount in GBB per transaction'
    )

    user_limit_basic_gbp = models.FloatField(
        'Maximum for basic users',
        help_text='Maximum amount a basic user is allowed to send per day in GBP'
    )

    user_limit_complete_gbp = models.FloatField(
        'Maximum for fully verified users',
        help_text='Maximum amount a fully verfied user is allowed to send per day in GBP'
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

    # USD Limits
    @property
    def transaction_min_usd(self):
        return self.exchange_rate_usd * self.transaction_min_gbp

    @property
    def transaction_max_usd(self):
        return self.exchange_rate_usd * self.transaction_max_gbp

    @property
    def user_limit_basic_usd(self):
        return self.exchange_rate_usd * self.user_limit_basic_gbp

    @property
    def user_limit_complete_usd(self):
        return self.exchange_rate_usd * self.user_limit_complete_gbp

    # SSL Limits
    @property
    def transaction_min_sll(self):
        return self.exchange_rate_sll * self.transaction_min_gbp

    @property
    def transaction_max_sll(self):
        return self.exchange_rate_sll * self.transaction_max_gbp

    # GHS Limits
    @property
    def transaction_min_ghs(self):
        return self.exchange_rate_ghs * self.transaction_min_gbp

    @property
    def transaction_max_ghs(self):
        return self.exchange_rate_ghs * self.transaction_max_gbp
