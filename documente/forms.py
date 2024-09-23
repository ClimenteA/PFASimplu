from django.forms import ModelForm, Textarea
from .models import DocumenteModel


class DocumenteForm(ModelForm):
    class Meta:
        model = DocumenteModel
        fields = "__all__"
        exclude = ["actualizat_la"]

        widgets = {
            "mentiuni": Textarea(attrs={"rows": "3"})
        }

