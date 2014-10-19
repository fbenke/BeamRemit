from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from beam.utils.log import log_error


class State(models.Model):

    RUNNING = 'UP'
    OUT_OF_CASH = 'DRY'
    OUTSIDE_BIZ_HOURS = 'OBH'

    APP_STATES = (
        (RUNNING, 'running'),
        (OUT_OF_CASH, 'out of cash'),
        (OUTSIDE_BIZ_HOURS, 'outside our business hours')
    )

    start = models.DateTimeField(
        'Start Time',
        auto_now_add=True,
        help_text='Time at which state came into effect'
    )

    end = models.DateTimeField(
        'End Time',
        blank=True,
        null=True,
        help_text='Time at which state has changed'
    )

    state = models.CharField(
        'State',
        max_length=4,
        choices=APP_STATES,
        default=RUNNING
    )


def get_current_state():
    try:
        return State.objects.get(end__isnull=True).state
    except ObjectDoesNotExist:
        log_error('ERROR State - No state object found.')
        raise ObjectDoesNotExist
