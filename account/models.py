from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from userena.models import UserenaBaseProfile


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    # Constants
    PDF = 'application/pdf'
    PNG = 'image/png'
    JPEG = 'image/jpeg'

    CONTENT_TYPES = (
        (PDF, 'pdf'),
        (PNG, 'png'),
        (JPEG, 'jpeg')
    )

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

    aws_passport_content_type = models.CharField(
        'Passport Document Format',
        max_length=15,
        blank=True,
        choices=CONTENT_TYPES,
        help_text='File type of passport document on aws'
    )
    aws_proof_of_residence_content_type = models.CharField(
        'Proof of Residence Document Format',
        max_length=15,
        blank=True,
        choices=CONTENT_TYPES,
        help_text='File type of passport document on aws'
    )

    passport_verified = models.BooleanField(default=False)

    proof_of_residence_verified = models.BooleanField(default=False)

    @property
    def is_complete(self):
        if (
            self.user.email == '' or self.user.first_name == '' or
            self.user.last_name == '' or not self.user.is_active or
            self.date_of_birth is None or self.street == '' or
            self.post_code == '' or self.city == '' or self.country == ''
            or not self.passport_verified or not self.proof_of_residence_verified
        ):
            return False
        return True
