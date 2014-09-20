from django import forms


class PricingForm(forms.ModelForm):
    def clean_markup(self):
        if not (0.0 <= self.cleaned_data['markup'] <= 1.0):
            raise forms.ValidationError('markup has to be a value between 0 and 1')
        return self.cleaned_data['markup']
