from django.forms import DateInput, ModelForm, TextInput

from utils.widgets import NumeFisierFileInput

from .models import IncasariModel


class IncasariForm(ModelForm):
    class Meta:
        model = IncasariModel
        fields = "__all__"
        exclude = ["actualizat_la", "factura", "user", "data_incasarii"]
        widgets = {
            "nume_incasare": TextInput(attrs={"autocomplete": "off"}),
            "data_inserarii": DateInput(format=("%m/%d/%Y"), attrs={"type": "date"}),
            "fisier": NumeFisierFileInput(),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Data operatiunii introdusa in formular este si data incasarii;
        # lasam data_incasarii NULL doar la inregistrarile "in asteptare".
        obj.data_incasarii = obj.data_inserarii
        if commit:
            obj.save()
        return obj
