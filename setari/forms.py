from django import forms
from django.forms import ModelForm
from .models import SetariModel


class SetariForm(ModelForm):
    class Meta:
        model = SetariModel
        exclude = ["actualizat_la"]
        widgets = {
            'scutit_cas': forms.CheckboxInput(),
            'scutit_cass': forms.CheckboxInput(),
            'scutit_impozit': forms.CheckboxInput(),
        }
        labels = {
            'scutit_cas': 'Scutit CAS',
            'scutit_cass': 'Scutit CASS',
            'scutit_impozit': 'Scutit Impozit',
        }
