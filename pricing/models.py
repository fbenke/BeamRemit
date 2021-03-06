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
            raise ObjectDoesNotExist


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
        if cls.objects.filter(site=site).exists():
            log_error('ERROR {} - Failed to end previous pricing.'.format(cls))
            raise ObjectDoesNotExist


def get_current_pricing(site):
    return get_current_object_by_site(Pricing, site)


def get_current_limit(site):
    return get_current_object_by_site(Limit, site)


def get_current_exchange_rate():
    return get_current_object(ExchangeRate)


def get_current_comparison():
    return get_current_object(Comparison)


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

    fee = models.FloatField(
        'Fixed Fee',
        help_text='Fixed Fee charged for the money transfer.'
    )

    site = models.ForeignKey(
        Site,
        related_name='pricing',
        help_text='Site associated with this pricing'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    @property
    def exchange_rate(self):
        return get_current_exchange_rate().exchange_rate(self.site) * (1 - self.markup)

    @property
    def fee_currency(self):
        return settings.SITE_SENDING_CURRENCY[self.site.id]

    def calculate_received_amount(self, sent_amount, country):

        unrounded_amount = sent_amount * self.exchange_rate

        # do country-specific rounding
        if country == settings.SIERRA_LEONE:
            return math.ceil(unrounded_amount / 10) * 10
        else:
            return math.ceil(unrounded_amount * 10) / 10


class ExchangeRate(models.Model):

    CURRENCY_FXR = {
        settings.USD: 'gbp_usd',
        settings.CEDI: 'gbp_ghs',
        settings.LEONE: 'gbp_sll',
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

    def _get_gbp_to_currency(self, currency):
        if currency == settings.GBP:
            return 1
        return getattr(self, self.CURRENCY_FXR[currency])

    def _get_exchange_rate(self, sending_currency, receiving_currency):
        gbp_to_sending_currency = self._get_gbp_to_currency(sending_currency)
        gbp_to_receiving_currency = self._get_gbp_to_currency(receiving_currency)
        return gbp_to_receiving_currency / gbp_to_sending_currency

    def exchange_amount(self, amount, sending_currency, receiving_currency):
        return amount * self._get_exchange_rate(sending_currency, receiving_currency)

    def exchange_rate(self, site):
        sending_currency = settings.SITE_SENDING_CURRENCY[site.id]
        receiving_currency = settings.SITE_RECEIVING_CURRENCY[site.id]
        return self._get_exchange_rate(sending_currency, receiving_currency)


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

    @property
    def sending_currency(self):
        return settings.SITE_SENDING_CURRENCY[self.site.id]

    @property
    def receiving_currency(self):
        return settings.SITE_RECEIVING_CURRENCY[self.site.id]

    @property
    def transaction_min_receiving(self):
        return get_current_pricing(self.site).exchange_rate * self.transaction_min

    @property
    def transaction_max_receiving(self):
        return get_current_pricing(self.site).exchange_rate * self.transaction_max


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
