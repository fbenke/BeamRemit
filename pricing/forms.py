from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

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
            self.fields['gbp_eur'].initial = exchange_rate.gbp_eur
            self.fields['gbp_ghs'].initial = exchange_rate.gbp_ghs
            self.fields['gbp_usd'].initial = exchange_rate.gbp_usd
            self.fields['gbp_sll'].initial = exchange_rate.gbp_sll
            self.fields['gbp_ngn'].initial = exchange_rate.gbp_ngn
        except (KeyError, ObjectDoesNotExist):
            pass


class LimitForm(forms.ModelForm):
    def clean(self):
        if not self.cleaned_data['transaction_min'] < self.cleaned_data['transaction_max']:
            raise forms.ValidationError('Minimum amount must be smaller than maximum amount.')
        if self.cleaned_data['sending_currency'] not in settings.SITE_SENDING_CURRENCY[self.cleaned_data['site'].id]:
            raise forms.ValidationError('Sending currency not supported for that Site.')
        return self.cleaned_data


class FeeForm(forms.ModelForm):
    def clean(self):
        if self.cleaned_data['currency'] not in settings.SITE_SENDING_CURRENCY[self.cleaned_data['site'].id]:
            raise forms.ValidationError('Sending currency not supported for that Site.')
        return self.cleaned_data
