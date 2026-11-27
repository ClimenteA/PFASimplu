from django import forms
from django.db import transaction
from django.forms import CheckboxInput, DateInput, ModelForm, Textarea

from .models import NOTA_TAXARE_INVERSA_VIES, FacturaModel, nota_taxare_inversa_vies


class FacturaForm(ModelForm):
    produse_sau_servicii = forms.JSONField(required=True)

    class Meta:
        model = FacturaModel
        fields = "__all__"
        exclude = ["user"]
        widgets = {
            "client_ue": CheckboxInput(attrs={"role": "switch"}),
            "nota": Textarea(attrs={"rows": "3"}),
            "data_emitere": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "data_scadenta": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("client_ue"):
            # Completam nota doar daca e goala sau contine inca textul implicit
            # (de exemplu la schimbarea limbii facturii), ca sa nu stergem o
            # mentiune scrisa manual de utilizator.
            nota = (cleaned.get("nota") or "").strip()
            if not nota or nota in NOTA_TAXARE_INVERSA_VIES.values():
                cleaned["nota"] = nota_taxare_inversa_vies(
                    cleaned.get("tip_factura") or ""
                )
        elif (cleaned.get("nota") or "").strip() in NOTA_TAXARE_INVERSA_VIES.values():
            # Clientul nu mai e VIES: stergem doar nota generata automat.
            cleaned["nota"] = ""
        return cleaned

    def clean_produse_sau_servicii(self):
        linii = self.cleaned_data["produse_sau_servicii"]
        if not isinstance(linii, list) or not linii:
            raise forms.ValidationError("Factura trebuie sa aiba cel putin o linie.")
        for linie in linii:
            if not isinstance(linie, dict) or not {
                "nume_produs_sau_serviciu",
                "cod_unitate",
                "numar_unitati",
                "pret_pe_unitate",
            }.issubset(linie):
                raise forms.ValidationError("Datele liniilor facturii sunt invalide.")
        return linii

    def save(self, commit=True):
        linii = self.cleaned_data.get("produse_sau_servicii", [])
        with transaction.atomic():
            factura = super().save(commit=commit)
            if commit:
                self._salveaza_linii(factura, linii)
        return factura

    @staticmethod
    def _salveaza_linii(factura, linii):
        existente = list(factura.linii.all())
        for index, linie in enumerate(linii):
            date = {
                "nume": str(linie["nume_produs_sau_serviciu"] or "")[:300],
                "cod_unitate": str(linie["cod_unitate"] or "HUR")[:10],
                "cantitate": linie["numar_unitati"],
                "pret_unitar": linie["pret_pe_unitate"],
            }
            if index < len(existente):
                obj = existente[index]
                for camp, valoare in date.items():
                    setattr(obj, camp, valoare)
                obj.save()
            else:
                factura.linii.create(**date)
        for obj in existente[len(linii) :]:
            obj.delete()
