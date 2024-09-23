from django.forms import ModelForm, DateInput, Textarea
from .models import FacturaModel


class FacturaForm(ModelForm):
    class Meta:
        model = FacturaModel
        fields = "__all__"
        widgets = {
            "nota": Textarea(attrs={"rows": "1"}),
            "data_emitere": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "data_scadenta": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
        }
