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
            log_error('ERROR {} - Failed to end previous pricing.').format(cls)


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
        help_text='Time at which comparison ended. If null, it represents the current pricing structure. ' +
                  'Only one row in this table can have a null value for this column.'
    )
