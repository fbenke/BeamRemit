from django.db import models

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile


class BeamProfile(UserenaBaseProfile):
    user = models.OneToOneField(
        User,
        unique=True,
        related_name='beam'
    )
    favourite_snack = models.CharField(
        _('favourite snack'),
        max_length=5)
