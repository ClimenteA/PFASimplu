import json
from django import forms
from django.forms import ModelForm
from utils.valuta import Valuta
from .models import SetariModel, validate_iban_length


class SetariForm(ModelForm):
    conturi_iban = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La editare valoarea vine ca lista din JSONField; o serializam
        # ca sa poata fi folosita ca initial pentru campul hidden din template.
        if isinstance(self.initial.get("conturi_iban"), list):
            self.initial["conturi_iban"] = json.dumps(self.initial["conturi_iban"])

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

    def clean_conturi_iban(self):
        raw = self.cleaned_data.get("conturi_iban")

        if not raw:
            return []

        try:
            conturi = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError("Lista de conturi IBAN este invalida.")

        if not isinstance(conturi, list):
            raise forms.ValidationError("Lista de conturi IBAN este invalida.")

        valute_valide = {choice.value for choice in Valuta}
        conturi_curatate = []
        valute_vazute = set()

        for cont in conturi:
            if not isinstance(cont, dict):
                raise forms.ValidationError("Lista de conturi IBAN este invalida.")

            iban = (cont.get("iban") or "").replace(" ", "").upper().strip()
            valuta = (cont.get("valuta") or Valuta.RON.value).upper().strip()

            if not iban:
                continue

            if valuta not in valute_valide:
                raise forms.ValidationError(f"Valuta {valuta} nu este valida.")

            if valuta in valute_vazute:
                raise forms.ValidationError(
                    f"Exista deja un cont IBAN pentru valuta {valuta}."
                )

            validate_iban_length(iban)

            valute_vazute.add(valuta)
            conturi_curatate.append({"valuta": valuta, "iban": iban})

        return conturi_curatate

    def clean(self):
        cleaned_data = super().clean()

        # Pastram si campul vechi iban sincronizat cu contul de RON
        # (sau primul cont disponibil) pentru compatibilitate.
        conturi = cleaned_data.get("conturi_iban") or []
        iban_ron = next(
            (c["iban"] for c in conturi if c["valuta"] == Valuta.RON.value), None
        )
        cleaned_data["iban"] = iban_ron or (conturi[0]["iban"] if conturi else None)

        return cleaned_data
