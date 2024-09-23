from django.forms import ModelForm, DateInput, TextInput
from .models import IncasariModel


class IncasariForm(ModelForm):
    class Meta:
        model = IncasariModel
        fields = "__all__"
        exclude = ["actualizat_la", "suma_in_ron"]        
        widgets = {
            "data_inserarii": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"})
        }
