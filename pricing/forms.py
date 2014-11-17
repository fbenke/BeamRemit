from django import forms
from django.core.exceptions import ObjectDoesNotExist

from pricing.models import ExchangeRate, get_current_object


class PricingForm(forms.ModelForm):

    def clean_markup(self):
        if not (0.0 <= self.cleaned_data['markup'] <= 1.0):
            raise forms.ValidationError('Markup has to be a value between 0 and 1')
        return self.cleaned_data['markup']


class ExchangeRateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ExchangeRateForm, self).__init__(*args, **kwargs)
        try:
            exchange_rate = get_current_object(ExchangeRate)
            self.fields['gbp_ghs'].initial = exchange_rate.gbp_ghs
            self.fields['gbp_usd'].initial = exchange_rate.gbp_usd
            self.fields['gbp_sll'].initial = exchange_rate.gbp_sll
        except (KeyError, ObjectDoesNotExist):
            pass


class LimitForm(forms.ModelForm):
    def clean(self):
        if not self.cleaned_data['transaction_min_gbp'] < self.cleaned_data['transaction_max_gbp']:
            raise forms.ValidationError('Minimum amount must be smaller than maximum amount.')
        return self.cleaned_data
