import math
import collections

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

from jsonfield import JSONField

from beam.utils.log import log_error


def get_current_object(cls, **kwargs):
    try:
        return cls.objects.get(end__isnull=True, **kwargs)
    except ObjectDoesNotExist:
        log_error('ERROR {} - No object found.'.format(cls))
        raise ObjectDoesNotExist


def end_previous_object(cls, **kwargs):
    try:
        previous_object = cls.objects.get(end__isnull=True, **kwargs)
        previous_object.end = timezone.now()
        previous_object.save()
    except ObjectDoesNotExist:
        pass


def get_current_exchange_rate():
    return get_current_object(ExchangeRate)


def get_current_comparison():
    return get_current_object(Comparison)


def get_current_pricing(site):
    return get_current_object(Pricing, site=site)


def get_current_limit(site, currency):
    return get_current_object(Limit, site=site, sending_currency=currency)


def get_current_limits(site):
    limits = Limit.objects.filter(site=site, end__isnull=True)
    if len(limits) != len(settings.SITE_SENDING_CURRENCY[site.id]):
        log_error('ERROR Limits - Missing limits for site {}.'.format(site.id))
    return limits


def get_current_fee(site, currency):
    return get_current_object(Fee, site=site, currency=currency)


def get_current_fees(site):
    fees = Fee.objects.filter(site=site, end__isnull=True)
    if len(fees) != len(settings.SITE_SENDING_CURRENCY[site.id]):
        log_error('ERROR Fees - Missing fees for site {}.'.format(site.id))
    return fees


class Fee(models.Model):

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

    site = models.ForeignKey(
        Site,
        related_name='fee',
        help_text='Site associated with this fee'
    )

    amount = models.FloatField(
        'Fixed Fee',
        help_text='Fixed Fee charged for the money transfer.'
    )

    currency = models.CharField(
        'Currency',
        max_length=4,
        choices=settings.SENT_CURRENCIES,
        help_text='Currency the fee is denominated in'
    )


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

    site = models.ForeignKey(
        Site,
        related_name='pricing',
        help_text='Site associated with this pricing'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    @property
    def exchange_rates(self):
        rates = get_current_exchange_rate().exchange_rates(self.site)
        rates = {k: v * (1 - self.markup) for k, v in rates.iteritems()}
        return rates

    def exchange_rate(self, sending_currency):
        receiving_currency = settings.SITE_RECEIVING_CURRENCY[self.site.id]
        return get_current_exchange_rate().get_exchange_rate(sending_currency, receiving_currency) * (1 - self.markup)

    def calculate_received_amount(self, sent_amount, sent_currency, country):

        unrounded_amount = sent_amount * self.exchange_rate(sent_currency)

        # do country-specific rounding
        if country == settings.SIERRA_LEONE:
            return math.ceil(unrounded_amount / 10) * 10
        else:
            return math.ceil(unrounded_amount * 10) / 10


class ExchangeRate(models.Model):

    CURRENCY_FXR = {
        settings.USD: 'gbp_usd',
        settings.EUR: 'gbp_eur',
        settings.CEDI: 'gbp_ghs',
        settings.LEONE: 'gbp_sll',
        settings.NAIRA: 'gbp_ngn'
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

    gbp_eur = models.FloatField(
        'GBP to EUR Exchange Rate',
        help_text='Exchange Rate from GBP to EUR without markup'
    )

    gbp_ngn = models.FloatField(
        'GBP to NGN Exchange Rate',
        help_text='Exchange Rate from GBP to NGN without markup'
    )

    def _get_gbp_to_currency(self, currency):
        if currency == settings.GBP:
            return 1
        return getattr(self, self.CURRENCY_FXR[currency])

    def get_exchange_rate(self, sending_currency, receiving_currency):
        try:
            gbp_to_sending_currency = self._get_gbp_to_currency(sending_currency)
            gbp_to_receiving_currency = self._get_gbp_to_currency(receiving_currency)
            return gbp_to_receiving_currency / gbp_to_sending_currency
        except ZeroDivisionError:
            log_error('ERROR Exchang Rate - Division By Zero.')
            return 0

    def exchange_amount(self, amount, sending_currency, receiving_currency):
        return amount * self.get_exchange_rate(sending_currency, receiving_currency)

    def exchange_rates(self, site):
        rates = {}
        receiving_currency = settings.SITE_RECEIVING_CURRENCY[site.id]
        for sending_currency in settings.SITE_SENDING_CURRENCY[site.id]:
            rates[sending_currency] = self.get_exchange_rate(sending_currency, receiving_currency)
        return rates


class Limit(models.Model):

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

    transaction_min = models.FloatField(
        'Minimum amount',
        help_text='Minimum remittance amount per transaction in sending currency'
    )

    transaction_max = models.FloatField(
        'Maximum amount',
        help_text='Maximum remittance amount per transaction in sending currency'
    )

    user_limit_basic = models.FloatField(
        'Maximum for basic users',
        help_text='Maximum amount a basic user is allowed to send per day in sending currency'
    )

    user_limit_complete = models.FloatField(
        'Maximum for fully verified users',
        help_text='Maximum amount a fully verfied user is allowed to send per day in sending currency'
    )

    site = models.ForeignKey(
        Site,
        related_name='limit',
        help_text='Site associated with this limit'
    )

    sending_currency = models.CharField(
        'Currency',
        max_length=4,
        choices=settings.SENT_CURRENCIES,
        help_text='Sending currency the limits are denominated in'
    )

    @property
    def receiving_currency(self):
        return settings.SITE_RECEIVING_CURRENCY[self.site.id]

    @property
    def transaction_min_receiving(self):
        return get_current_pricing(self.site).exchange_rate(self.sending_currency) * self.transaction_min

    @property
    def transaction_max_receiving(self):
        return get_current_pricing(self.site).exchange_rate(self.sending_currency) * self.transaction_max


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
