from django.forms import DateInput, ModelForm, TextInput

from cheltuieli.models import CheltuialaModel
from utils.widgets import NumeFisierFileInput


class InventarForm(ModelForm):
    class Meta:
        model = CheltuialaModel
        fields = [
            "nume_cheltuiala",
            "modalitate_iesire_din_uz",
            "data_iesirii_din_uz",
            "document_justificativ_iesire_din_uz",
        ]

        widgets = {
            "nume_cheltuiala": TextInput(attrs={"readonly": "true"}),
            "data_iesirii_din_uz": DateInput(
                format=("%m/%d/%Y"), attrs={"type": "date", "required": "true"}
            ),
            "document_justificativ_iesire_din_uz": NumeFisierFileInput(),
        }
