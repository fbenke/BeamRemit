import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db import transaction as dbtransaction
from django.utils import timezone
from django.utils.timezone import utc
from django_countries.fields import CountryField

from userena.models import UserenaBaseProfile

from transaction.models import Transaction

from account.utils import AccountException

from beam.utils.general import log_error

from pricing.models import Limit, get_current_object


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    PASSPORT = 'PAS'
    PROOF_OF_RESIDENCE = 'POR'

    DOCUMENT_TYPES = (PASSPORT, PROOF_OF_RESIDENCE)

    DOCUMENT_VERBAL = {
        PASSPORT: 'Passport',
        PROOF_OF_RESIDENCE: 'Proof of Residence'
    }

    DOCUMENT_TYPE_CHOICES = (
        (PASSPORT, DOCUMENT_VERBAL[PASSPORT]),
        (PROOF_OF_RESIDENCE, DOCUMENT_VERBAL[PROOF_OF_RESIDENCE])
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

        with dbtransaction.atomic():

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

    def transaction_limit_exceeded(self, new_amount=0):
        try:
            now = timezone.now()
            today = datetime.datetime(now.year, now.month, now.day).replace(tzinfo=utc)

            transactions = Transaction.objects.filter(
                sender=self.user.id,
                state__in=(Transaction.PAID, Transaction.PROCESSED),
                paid_at__gte=today
            )

            amount = new_amount
            for t in transactions:
                amount = amount + t.amount_gbp

            return amount > get_current_object(Limit).daily_limit_gbp

        except TypeError:

            log_error('ERROR - Adding up transaction amounts for user {}'.format(self.user.id))
            raise AccountException


class DocumentStatusChange(models.Model):
    class Meta:
        ordering = ['-changed_at']

    # TODO: add valid reasons
    INVALID_PASSPORT = 'INP'
    CREDIT_NOT_ACCEPTED = 'CRE'
    MOBILE_NOT_ACCEPTED = 'PHO'
    INVALID_FORMAT = 'INF'
    CONTRADICTION = 'CON'
    LOW_RESOLUTION = 'QUA'
    MISC = 'MIS'

    REASONS_PAS = (
        (INVALID_PASSPORT, 'Invalid Passport'),
    )

    REASONS_POR = (
        (CREDIT_NOT_ACCEPTED, 'Credit Card not accepted'),
        (MOBILE_NOT_ACCEPTED, 'Phone Bill not accepted')
    )

    REASONS_GENERAL = (
        (INVALID_FORMAT, 'Invalid Format'),
        (LOW_RESOLUTION, 'Low Resolution Document'),
        (MISC, 'Miscellaneous'),
        (CONTRADICTION, 'Contradicting Information')
    )

    REASONS = REASONS_PAS + REASONS_POR + REASONS_GENERAL

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
