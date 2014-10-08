from django import forms


class ProfileModelForm(forms.ModelForm):

    send_passport_mail = forms.BooleanField(required=False, initial=True)
    send_proof_of_residence_mail = forms.BooleanField(required=False, initial=True)
