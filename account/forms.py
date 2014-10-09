from django import forms

from account.models import DocumentStatusChange
from account.models import BeamProfile as Profile


class ProfileModelForm(forms.ModelForm):

    DOCUMENT_FIELD = {
        Profile.PASSPORT_FIELD: ('send_passport_mail', 'passport_reason'),
        Profile.PROOF_OF_RESIDENCE_FIELD: ('send_proof_of_residence_mail', 'proof_of_residence_reason')
    }

    send_passport_mail = forms.BooleanField(required=False, initial=True)
    send_proof_of_residence_mail = forms.BooleanField(required=False, initial=True)
    passport_reason = forms.ChoiceField(
        choices=DocumentStatusChange.REASONS_GENERAL + DocumentStatusChange.REASONS_PAS)
    proof_of_residence_reason = forms.ChoiceField(
        choices=DocumentStatusChange.REASONS_GENERAL + DocumentStatusChange.REASONS_POR)
