from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from userena.models import UserenaBaseProfile


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    user = models.OneToOneField(
        User,
        unique=True,
        related_name='profile'
    )

    date_of_birth = models.DateField(
        'Date of Birth',
        null=True,
        blank=True,
        help_text='Date of Birth'
    )

    street = models.CharField(
        'Street and number',
        max_length=50,
        blank=True,
        help_text='Street and number'
    )

    post_code = models.CharField(
        'Post Code',
        max_length=10,
        blank=True,
        help_text='Post Code'
    )

    city = models.CharField(
        'City',
        max_length=40,
        blank=True,
        help_text='City'
    )

    country = CountryField(
        'Country',
        blank=True,
        help_text='Country'
    )

    @property
    def is_complete(self):
        # if (
        #     self.user.email == '' or self.user.first_name == '' or
        #     self.user.last_name == '' or not self.user.is_active or
        #     self.date_of_birth is None or self.street == '' or
        #     self.post_code == '' or self.city == '' or self.country == ''
        # ):
        #     return False
        return True
