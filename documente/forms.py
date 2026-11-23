from django import forms
from django.forms import ModelForm, Textarea
from django.utils import timezone
import datetime
from .models import DocumenteModel, validate_year


class DocumenteForm(ModelForm):
    # In UI se alege o data (date input); in baza de date se salveaza doar
    # anul (IntegerField), ca pana acum - restul codului lucreaza cu anul.
    document_pentru_anul = forms.DateField(
        required=False,
        label="Document pentru data",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La editare, anul salvat (int) devine 1 ianuarie a acelui an.
        anul = self.initial.get("document_pentru_anul")
        if isinstance(anul, int):
            self.initial["document_pentru_anul"] = datetime.date(anul, 1, 1)
        # La adaugare, implicit data curenta.
        if self.instance.pk is None and not self.initial.get("document_pentru_anul"):
            self.initial["document_pentru_anul"] = timezone.now().date()

    def clean_document_pentru_anul(self):
        data = self.cleaned_data.get("document_pentru_anul")
        if not data:
            return None
        validate_year(data.year)
        return data.year

    class Meta:
        model = DocumenteModel
        fields = "__all__"
        exclude = ["actualizat_la", "user"]

        widgets = {
            "mentiuni": Textarea(attrs={"rows": "3"})
        }

