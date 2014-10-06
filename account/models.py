from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from userena.models import UserenaBaseProfile

from account.utils import AccountException


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    EMPTY = 'EMP'
    UPLOADED = 'UPL'
    VERIFIED = 'VER'
    FAILED = 'FAL'

    DOCUMENT_STATES = (
        (EMPTY, 'not provided'),
        (UPLOADED, 'uploaded'),
        (VERIFIED, 'verified'),
        (FAILED, 'failed')
    )

    PASSPORT = 'passport'
    PROOF_OF_RESIDENCE = 'proof_of_residence'

    DOCUMENT_TYPES = (PASSPORT, PROOF_OF_RESIDENCE)

    DOCUMENT_FIELD_MAPPING = {
        PASSPORT: 'passport_state',
        PROOF_OF_RESIDENCE: 'proof_of_residence_state'
    }

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

    passport_state = models.CharField(
        'Passport Status',
        max_length=3,
        choices=DOCUMENT_STATES,
        default=EMPTY
    )

    proof_of_residence_state = models.CharField(
        'Proof of Residence Status',
        max_length=3,
        choices=DOCUMENT_STATES,
        default=EMPTY
    )

    def get_document_states(self):
        states = {}
        for d in self.DOCUMENT_TYPES:
            states[d] = getattr(self, self.DOCUMENT_FIELD_MAPPING[d])
        return states

    def update_document_states(self, documents):
        for d in documents:
            if d not in self.DOCUMENT_TYPES:
                raise AccountException
            setattr(self, self.DOCUMENT_FIELD_MAPPING[d], self.UPLOADED)
        self.save()

    @property
    def is_complete(self):
        if (
            self.user.email == '' or self.user.first_name == '' or
            self.user.last_name == '' or not self.user.is_active or
            self.date_of_birth is None or self.street == '' or
            self.post_code == '' or self.city == '' or self.country == ''
            or self.passport_state == self.EMPTY
            or self.proof_of_residence_state == self.EMPTY
        ):
            return False
        return True

    @property
    def is_verified(self):
        if (
            not self.is_complete or
            self.passport_state != self.VERIFIED or
            self.proof_of_residence_state != self.VERIFIED
        ):
            return False
        return True
