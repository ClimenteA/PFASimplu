import json

from django import forms
from django.db import transaction
from django.forms import ModelForm

from utils.valuta import Valuta

from .models import ContBancar, SetariModel, validate_iban_length


class SetariForm(ModelForm):
    conturi_iban = forms.CharField(required=False, widget=forms.HiddenInput())
    caen_secondar_1 = forms.CharField(required=False, max_length=4)
    caen_secondar_2 = forms.CharField(required=False, max_length=4)
    caen_secondar_3 = forms.CharField(required=False, max_length=4)
    caen_secondar_4 = forms.CharField(required=False, max_length=4)
    caen_secondar_5 = forms.CharField(required=False, max_length=4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.initial.get("conturi_iban"), list):
            self.initial["conturi_iban"] = json.dumps(self.initial["conturi_iban"])
        elif self.instance.pk:
            self.initial["conturi_iban"] = json.dumps(
                [
                    {"valuta": c.valuta, "iban": c.iban}
                    for c in self.instance.conturi.all()
                ]
            )
        if self.instance.pk:
            for i, cod in enumerate(self.instance.caen_secondare or [], start=1):
                self.initial[f"caen_secondar_{i}"] = cod

    class Meta:
        model = SetariModel
        exclude = ["actualizat_la", "user", "caen_secondare"]
        widgets = {
            "cod_tva_intracomunitar": forms.TextInput(
                attrs={"placeholder": "ex. 52937756 (fara RO)"}
            ),
            "cont_iban_trezoreria": forms.TextInput(
                attrs={"placeholder": "ex. RO41TREZ40620A100101XTVA"}
            ),
        }
        labels = {
            "scutit_cas": "Scutit CAS",
            "scutit_cass": "Scutit CASS",
            "scutit_impozit": "Scutit Impozit",
            "cod_tva_intracomunitar": "Cod TVA intracomunitar (art. 317)",
            "cont_iban_trezoreria": "IBAN trezorerie pentru plata TVA",
        }

    def clean_cod_tva_intracomunitar(self):
        value = (self.cleaned_data.get("cod_tva_intracomunitar") or "").strip().upper()
        value = value.removeprefix("RO").replace(" ", "")
        if value and not value.isdigit():
            raise forms.ValidationError(
                "Codul TVA intracomunitar trebuie sa fie numeric (fara prefixul RO)."
            )
        return value or None

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
        curatate = []
        vazute = set()
        for cont in conturi:
            if not isinstance(cont, dict):
                raise forms.ValidationError("Lista de conturi IBAN este invalida.")
            iban = (cont.get("iban") or "").replace(" ", "").upper().strip()
            valuta = (cont.get("valuta") or Valuta.RON.value).upper().strip()
            if not iban:
                continue
            if valuta not in valute_valide:
                raise forms.ValidationError(f"Valuta {valuta} nu este valida.")
            if valuta in vazute:
                raise forms.ValidationError(
                    f"Exista deja un cont IBAN pentru valuta {valuta}."
                )
            validate_iban_length(iban)
            vazute.add(valuta)
            curatate.append({"valuta": valuta, "iban": iban})
        return curatate

    def save(self, commit=True):
        conturi = self.cleaned_data.get("conturi_iban") or []
        caen = [
            self.cleaned_data.get(f"caen_secondar_{i}")
            for i in range(1, 6)
            if self.cleaned_data.get(f"caen_secondar_{i}")
        ]
        with transaction.atomic():
            obj = super().save(commit=commit)
            if commit:
                obj.caen_secondare = caen
                obj.save(update_fields=["caen_secondare"])
                obj.conturi.all().delete()
                for cont in conturi:
                    ContBancar.objects.create(
                        setari=obj, valuta=cont["valuta"], iban=cont["iban"]
                    )
        return obj
