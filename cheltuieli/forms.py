from django.forms import ModelForm, DateInput, TextInput
from .models import CheltuialaModel


class CheltuieliForm(ModelForm):
    class Meta:
        model = CheltuialaModel
        fields = "__all__"
        exclude = [
            "actualizat_la",
            "suma_in_ron",
            "deducere_in_ron",
            "baza_in_lei",
            "tva_autolichidata",
            "curs_bnr_aplicat",  # completat automat din cursvalutarbnr
            "user",
        ]
        widgets = {
            "cod_de_clasificare": TextInput(attrs={"placeholder": "2.2.9."}),
            "nume_cheltuiala": TextInput(attrs={"autocomplete": "off"}),
            "data_inserarii": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "data_punerii_in_functiune": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "data_facturii": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "furnizor_denumire": TextInput(attrs={"autocomplete": "off", "placeholder": "ex. CORTECS GMBH"}),
            "furnizor_cod_fiscal": TextInput(attrs={"autocomplete": "off", "placeholder": "UE: ATU77164426 / non-UE: 27-0805829"}),
            "numar_factura": TextInput(attrs={"autocomplete": "off", "placeholder": "ex. PBW-2026-003576"}),
        }
        labels = {
            "tip_achizitie": "Origine furnizor",
            "furnizor_denumire": "Denumire furnizor",
            "furnizor_cod_fiscal": "Cod TVA / cod fiscal furnizor",
            "furnizor_tara": "Tara furnizor",
            "numar_factura": "Numar factura",
            "data_facturii": "Data facturii (exigibilitate TVA)",
        }
