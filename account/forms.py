from django import forms

from models import BeamProfile


class ProfileModelForm(forms.ModelForm):

    ADMIN_CHOICES = (
        (BeamProfile.UPLOADED, 'uploaded'),
        (BeamProfile.VERIFIED, 'verified'),
        (BeamProfile.FAILED, 'failed')
    )

    passport_state = forms.ChoiceField(choices=ADMIN_CHOICES)
    proof_of_residence_state = forms.ChoiceField(choices=ADMIN_CHOICES)
