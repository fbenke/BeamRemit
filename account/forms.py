from django import forms

from account.models import DocumentStatusChange
from account.models import BeamProfile as Profile


class ProfileModelForm(forms.ModelForm):

    DOCUMENT_FIELD = {
        Profile.IDENTIFICATION_FIELD: ('send_identification_mail', 'identification_reason'),
        Profile.PROOF_OF_RESIDENCE_FIELD: ('send_proof_of_residence_mail', 'proof_of_residence_reason')
    }

    send_identification_mail = forms.BooleanField(required=False, initial=True)
    send_proof_of_residence_mail = forms.BooleanField(required=False, initial=True)
    identification_reason = forms.ChoiceField(
        choices=DocumentStatusChange.REASONS_IDENTIFICATION + DocumentStatusChange.REASONS_GENERAL)
    proof_of_residence_reason = forms.ChoiceField(
        choices=DocumentStatusChange.REASONS_PROOF_OF_RESIDENCE + DocumentStatusChange.REASONS_GENERAL)
