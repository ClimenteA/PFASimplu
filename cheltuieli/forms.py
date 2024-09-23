from django.forms import ModelForm, DateInput, TextInput
from .models import CheltuialaModel


class CheltuieliForm(ModelForm):
    class Meta:
        model = CheltuialaModel
        fields = "__all__"
        exclude = ["actualizat_la", "suma_in_ron", "deducere_in_ron"]
        widgets = {
            "cod_de_clasificare": TextInput(attrs={"placeholder": "2.2.9."}),
            "nume_cheltuiala": TextInput(attrs={"autocomplete": "off"}),
            "data_inserarii": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "data_punerii_in_functiune": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
        }
