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

from pricing.models import ExchangeRate, get_current_object

from beam.utils.log import log_error


class BeamProfile(UserenaBaseProfile):
    ''' represents a sender user profile '''

    IDENTIFICATION = 'PAS'
    PROOF_OF_RESIDENCE = 'POR'

    DOCUMENT_TYPES = (IDENTIFICATION, PROOF_OF_RESIDENCE)

    DOCUMENT_VERBAL = {
        IDENTIFICATION: 'Identification Document',
        PROOF_OF_RESIDENCE: 'Proof of Residence'
    }

    DOCUMENT_TYPE_CHOICES = (
        (IDENTIFICATION, DOCUMENT_VERBAL[IDENTIFICATION]),
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

    IDENTIFICATION_FIELD = 'identification_state'
    PROOF_OF_RESIDENCE_FIELD = 'proof_of_residence_state'

    DOCUMENT_FIELDS = (IDENTIFICATION_FIELD, PROOF_OF_RESIDENCE_FIELD)

    DOCUMENT_FIELD_MAPPING = {
        IDENTIFICATION: IDENTIFICATION_FIELD,
        PROOF_OF_RESIDENCE: PROOF_OF_RESIDENCE_FIELD
    }

    FIELD_DOCUMENT_MAPPING = {
        IDENTIFICATION_FIELD: IDENTIFICATION,
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
        max_length=50,
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

    identification_state = models.CharField(
        'Identification Document Status',
        max_length=3,
        choices=DOCUMENT_STATE_CHOICES,
        default=EMPTY
    )

    identification_number = models.CharField(
        'Identification Document Number',
        max_length=30,
        blank=True
    )

    identification_issue_date = models.DateField(
        'Identification Document Date of Issue',
        null=True,
        blank=True
    )

    identification_expiry_date = models.DateField(
        'Identification Document Expiry Date',
        null=True,
        blank=True
    )

    proof_of_residence_state = models.CharField(
        'Proof of Residence Status',
        max_length=3,
        choices=DOCUMENT_STATE_CHOICES,
        default=EMPTY
    )

    accepted_privacy_policy = models.BooleanField(
        'Privacy Policy accepted',
        default=True
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
            self.identification_state in (self.EMPTY, self.FAILED) or
            self.proof_of_residence_state in (self.EMPTY, self.FAILED)
        ):
            return False
        return True

    @property
    def documents_verified(self):
        if (
            not self.information_complete or
            self.identification_state != self.VERIFIED or
            self.proof_of_residence_state != self.VERIFIED
        ):
            return False
        return True

    def todays_transaction_volume(self, new_amount=0, new_currency=None):
        try:
            now = timezone.now()
            today = datetime.datetime(now.year, now.month, now.day).replace(tzinfo=utc)

            transactions = Transaction.objects.filter(
                sender=self.user.id,
                state__in=(Transaction.PAID, Transaction.PROCESSED),
                paid_at__gte=today
            )

            amount = 0

            if new_amount:
                amount = get_current_object(ExchangeRate).convert_to_base_currency(new_amount, new_currency)

            for t in transactions:
                amount = amount + t.exchange_rate.convert_to_base_currency(t.sent_amount, t.sent_currency)

            return amount

        except TypeError:

            log_error('ERROR - Adding up transaction amounts for user {}'.format(self.user.id))
            raise AccountException


class DocumentStatusChange(models.Model):
    class Meta:
        ordering = ['-changed_at']

    INVALID_IDENTIFICATION = 'INI'
    EXPIRED_IDENTIFICATION = 'EXI'
    INCOMPLETE_IDENTIFICATION = 'INC'
    EXPIRED_PROOF_OF_RESIDENCE = 'EXP'
    ADDRESS_MISMATCH = 'ADM'
    INVALID_PROOF_OF_RESIDENCE = 'INP'
    CONTRADICTION = 'CON'
    LOW_QUALITY = 'LOW'
    MISCELLANEOUS = 'MIS'

    REASONS_IDENTIFICATION = (
        (INVALID_IDENTIFICATION, 'Invalid Identification'),
        (EXPIRED_IDENTIFICATION, 'Expired Identification'),
        (INCOMPLETE_IDENTIFICATION, 'Incomplete Identification')
    )

    REASONS_PROOF_OF_RESIDENCE = (
        (EXPIRED_PROOF_OF_RESIDENCE, 'Expired POR'),
        (ADDRESS_MISMATCH, 'Address Mismatch on POR'),
        (INVALID_PROOF_OF_RESIDENCE, 'Invalid POR')
    )

    REASONS_GENERAL = (
        (LOW_QUALITY, 'Low Quality'),
        (CONTRADICTION, 'Contradicting Information'),
        (MISCELLANEOUS, 'Miscellaneous')
    )

    REASONS = REASONS_IDENTIFICATION + REASONS_PROOF_OF_RESIDENCE + REASONS_GENERAL

    REASON_VERBAL = {
        INVALID_IDENTIFICATION: 'the file does not depict an identity document issued by your country. We accept passports, driver licenses and national id cards.',
        EXPIRED_IDENTIFICATION: 'the document is expired.',
        INCOMPLETE_IDENTIFICATION: 'important parts of the document are not visible (i.e. document number or picture) or entirely missing (i.e. second side of an id card).',
        EXPIRED_PROOF_OF_RESIDENCE: 'the document is older than 3 months.',
        ADDRESS_MISMATCH: 'the address on the document does not match the address you provided.',
        INVALID_PROOF_OF_RESIDENCE: 'the document cannot be accepted as proof of residence. Please upload a utility bill, bank statement or tax return.',
        LOW_QUALITY: 'the document quality is too low.',
        CONTRADICTION: 'the profile information and information on the document were contradicting.',
        MISCELLANEOUS: 'something was wrong with the document. A member of the support team will contact you in a separate email.'
    }

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
