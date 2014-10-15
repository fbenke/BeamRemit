import collections

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from jsonfield import JSONField

from beam.utils.general import log_error


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

    gbp_ghs = models.FloatField(
        'GBP to GHS Exchange Rate',
        help_text='Exchange Rate from GBP to GHS without markup'
    )

    fee = models.FloatField(
        'Fixed Fee',
        help_text='Fixed Fee charged for the money transfer.'
    )

    def __unicode__(self):
        return '{}'.format(self.id)

    @property
    def exchange_rate(self):
        return self.gbp_ghs * (1 - self.markup)


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
        self.exchange_rate = get_current_object(Pricing).gbp_ghs * (1 - get_current_object(Pricing).markup)

    max_gbp = models.FloatField(
        'Maximum amount in GBP ',
        help_text='Maximum remittance amount in GBB per transaction'
    )

    min_gbp = models.FloatField(
        'Minimum amount in GBP ',
        help_text='Minimum remittance amount in GBB per transaction'
    )

    daily_limit_gbp_basic = models.FloatField(
        'Maximum for basic users',
        help_text='Maximum amount a basic user is allowed to send per day in GBP'
    )

    daily_limit_gbp_complete = models.FloatField(
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

    @property
    def min_ghs(self):
        return self.exchange_rate * self.min_gbp

    @property
    def max_ghs(self):
        return self.exchange_rate * self.max_gbp

    @property
    def daily_limit_ghs_basic(self):
        return self.exchange_rate * self.daily_limit_gbp_basic

    @property
    def daily_limit_ghs_complete(self):
        return self.exchange_rate * self.daily_limit_gbp_complete
