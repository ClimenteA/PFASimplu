from django import forms
from django.forms import ModelForm, Textarea
from django.utils import timezone

from utils.widgets import NumeFisierFileInput

from .models import DocumenteModel, validate_year


class DocumenteForm(ModelForm):
    # UI-ul afiseaza o data; in baza se pastreaza data_document.
    document_pentru_anul = forms.DateField(
        required=False,
        label="Document pentru data",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    # Optiune de upload: parsarea face parte din serviciu, nu din model.
    parse_tip_document = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.data_document:
            self.initial["document_pentru_anul"] = self.instance.data_document
        if self.instance.pk is None and not self.initial.get("document_pentru_anul"):
            self.initial["document_pentru_anul"] = timezone.now().date()

    def clean_document_pentru_anul(self):
        data = self.cleaned_data.get("document_pentru_anul")
        if not data:
            return None
        validate_year(data.year)
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.data_document = self.cleaned_data.get("document_pentru_anul")
        if commit:
            obj.save()
        return obj

    class Meta:
        model = DocumenteModel
        fields = "__all__"
        exclude = ["actualizat_la", "user", "data_document"]

        widgets = {
            "mentiuni": Textarea(attrs={"rows": "3"}),
            "fisier": NumeFisierFileInput(),
        }
