from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from userena.models import UserenaBaseProfile

from account.utils import AccountException


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    PASSPORT = 'PAS'
    PROOF_OF_RESIDENCE = 'POR'

    DOCUMENT_TYPES = (PASSPORT, PROOF_OF_RESIDENCE)

    DOCUMENT_DESCRIPTION = {
        PASSPORT: 'Passport',
        PROOF_OF_RESIDENCE: 'Proof of Residence'
    }

    DOCUMENT_TYPE_CHOICES = (
        (PASSPORT, DOCUMENT_DESCRIPTION[PASSPORT]),
        (PROOF_OF_RESIDENCE, DOCUMENT_DESCRIPTION[PROOF_OF_RESIDENCE])
    )

    EMPTY = 'EMP'
    UPLOADED = 'UPL'
    VERIFIED = 'VER'
    FAILED = 'FAL'
    
    DOCUMENT_STATES = (EMPTY, UPLOADED, VERIFIED, FAILED)

    DOCUMENT_STATE_CHOICES = (
        (EMPTY, 'not provided'),
        (UPLOADED, 'uploaded'),
        (VERIFIED, 'verified'),
        (FAILED, 'failed')
    )

    PASSPORT_FIELD = 'passport_state'
    PROOF_OF_RESIDENCE_FIELD = 'proof_of_residence_state'

    DOCUMENT_FIELDS = (PASSPORT_FIELD, PROOF_OF_RESIDENCE_FIELD)

    DOCUMENT_FIELD_MAPPING = {
        PASSPORT: PASSPORT_FIELD,
        PROOF_OF_RESIDENCE: PROOF_OF_RESIDENCE_FIELD
    }

    FIELD_DOCUMENT_MAPPING = {
        PASSPORT_FIELD: PASSPORT,
        PROOF_OF_RESIDENCE_FIELD: PROOF_OF_RESIDENCE
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
        choices=DOCUMENT_STATE_CHOICES,
        default=EMPTY
    )

    proof_of_residence_state = models.CharField(
        'Proof of Residence Status',
        max_length=3,
        choices=DOCUMENT_STATE_CHOICES,
        default=EMPTY
    )

    def get_document_state(self, document):
        return getattr(self, self.DOCUMENT_FIELD_MAPPING[document])

    def get_document_states(self):
        states = {}
        for d in self.DOCUMENT_TYPES:
            states[d] = getattr(self, self.DOCUMENT_FIELD_MAPPING[d])
        return states

    def update_document_state(self, document, state, user='user', reason=''):

        if (document not in self.DOCUMENT_TYPES) or (state not in self.DOCUMENT_STATES):
            raise AccountException()

        setattr(self, self.DOCUMENT_FIELD_MAPPING[document], state)

        record = DocumentStatusChange(
            profile=self,
            changed_by=user,
            document_type=document,
            changed_to=state,
            reason=reason
        )

        self.save()
        record.save()

    @property
    def information_complete(self):
        if (
            self.user.email == '' or self.user.first_name == '' or
            self.user.last_name == '' or not self.user.is_active or
            self.date_of_birth is None or self.street == '' or
            self.post_code == '' or self.city == '' or self.country == ''
        ):
            return False
        return True

    @property
    def documents_provided(self):
        if (
            self.passport_state in (self.EMPTY, self.FAILED) or
            self.proof_of_residence_state in (self.EMPTY, self.FAILED)
        ):
            return False
        return True

    @property
    def documents_verified(self):
        if (
            not self.information_complete or
            self.passport_state != self.VERIFIED or
            self.proof_of_residence_state != self.VERIFIED
        ):
            return False
        return True


class DocumentStatusChange(models.Model):

    class Meta:
        ordering = ['-changed_at']

    # TODO: add valid reasons
    REASONS = (
        ('CRE', 'Credit Card not accepted'),
        ('PHO', 'Phone Bill not accepted'),
        ('QUA', 'Low Resolution Document'),
        ('MIS', 'Miscellaneous')
    )

    profile = models.ForeignKey(
        BeamProfile,
        related_name='document_status_change',
        help_text='Profile associated with that document status change.'
    )

    changed_by = models.CharField(
        'Changed by',
        max_length=50,
        help_text='Who initiated document status change'
    )

    document_type = models.CharField(
        'Document Type',
        max_length=3,
        choices=BeamProfile.DOCUMENT_TYPE_CHOICES,
        help_text='Document type for which status has changed'
    )

    changed_at = models.DateTimeField(
        'Changed at',
        auto_now_add=True,
        help_text='Time at which document status was changed'
    )

    changed_to = models.CharField(
        'Changed to',
        max_length=3,
        choices=BeamProfile.DOCUMENT_STATE_CHOICES,
        help_text='New document status'
    )

    reason = models.CharField(
        'Reason',
        max_length=3,
        choices=REASONS,
        blank=True,
        help_text='Reason for rejection. Only used when state changes to \'failed\''
    )
