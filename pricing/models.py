from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

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
        try:
            return Pricing.objects.get(end__isnull=True)
        except ObjectDoesNotExist:
            log_error('ERROR Pricing - No pricing object found.')

    @staticmethod
    def end_previous_pricing():
        try:
            previous_pricing = Pricing.objects.get(end__isnull=True)
            previous_pricing.end = timezone.now()
            previous_pricing.save()
        except ObjectDoesNotExist:
            if Pricing.objects.all().exists():
                log_error('ERROR Pricing - Failed to end previous pricing.')
