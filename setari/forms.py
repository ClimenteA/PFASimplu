from django.forms import ModelForm
from .models import SetariModel



class SetariForm(ModelForm):
    class Meta:
        model = SetariModel
        fields = "__all__"
        exclude = ["actualizat_la"]
