from django import forms


class PricingForm(forms.ModelForm):
    def clean_markup(self):
        if not (0.0 <= self.cleaned_data['markup'] <= 1.0):
            raise forms.ValidationError('Markup has to be a value between 0 and 1')
        return self.cleaned_data['markup']


class LimitForm(forms.ModelForm):
    def clean(self):
        if not self.cleaned_data['transaction_min_gbp'] < self.cleaned_data['transaction_max_gbp']:
            raise forms.ValidationError('Minimum amount must be smaller than maximum amount.')
        return self.cleaned_data

