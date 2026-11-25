from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from utils.decimale import D, rotund2
from utils.files import get_save_path
from utils.models import UserOwnedModel


class TipDocument(models.TextChoices):
    DOCUMENT_UTIL = "UTIL", _("Document util")
    DOVADA_PLATA_TAXE_SI_IMPOZITE = "PLATA_TAXE", _("Dovada plata taxe si impozite")
    DECLARATIE_UNICA_212 = "D212", _("Declaratie unica 212")
    DECLARATIE_UNICA_212_DOVADA_INCARCARE = (
        "D212_DOVADA",
        _("Declaratie unica 212 dovada incarcare"),
    )
    DECLARATIE_INREGISTRARE_SCOP_TVA_097 = (
        "D097",
        _("Declaratie inregistrare PFA in scop TVA 097"),
    )
    DECLARATIE_INREGISTRARE_SCOP_TVA_097_DOVADA_INCARCARE = (
        "D097_DOVADA",
        _("Declaratie inregistrare PFA in scop TVA 097 dovada incarcare"),
    )
    DECLARATIE_TVA_DECONT_300 = "D300", _("Declaratie decont TVA 300")
    DECLARATIE_TVA_DECONT_300_DOVADA_INCARCARE = (
        "D300_DOVADA",
        _("Declaratie decont TVA 300 dovada incarcare"),
    )
    DECLARATIE_TVA_DECONT_SPECIAL_301 = "D301", _("Declaratie decont special TVA 301")
    DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA = (
        "D301_RECIPISA",
        _("Declaratie decont special TVA 301 recipisa"),
    )
    DECLARATIE_TVA_RECAPITULATIVA_390 = "D390", _("Declaratie recapitulativa TVA 390")
    DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA = (
        "D390_RECIPISA",
        _("Declaratie recapitulativa TVA 390 recipisa"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392A = (
        "D392A",
        _("Declaratie activitate financiara 392A"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392A_DOVADA_INCARCARE = (
        "D392A_DOVADA",
        _("Declaratie activitate financiara 392A dovada incarcare"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392B = (
        "D392B",
        _("Declaratie activitate financiara 392B"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392B_DOVADA_INCARCARE = (
        "D392B_DOVADA",
        _("Declaratie activitate financiara 392B dovada incarcare"),
    )
    DECLARATIE_OBLIGATI_PLATA_PENTRU_SALARIATI_112 = (
        "D112",
        _("Declaratie obligatii de plata pentru salariati 112"),
    )
    DECLARATIE_OBLIGATI_PLATA_PENTRU_SALARIATI_212_DOVADA_INCARCARE = (
        "D112_DOVADA",
        _("Declaratie obligatii de plata pentru salariati 112 dovada incarcare"),
    )


def validate_year(value):
    if value < 2000 or value > 2500:
        raise ValidationError(f"{value} nu este un an valid.")


class DocumenteModel(UserOwnedModel):
    tip_document = models.CharField(
        max_length=30, choices=TipDocument, default=TipDocument.DOCUMENT_UTIL
    )
    # Data documentului (in versiunea veche se pastra doar anul, ca intreg).
    data_document = models.DateField(null=True, blank=True)
    # Suma platita catre stat, extrasa din dovada de plata (camp structurat,
    # nu text parsat prin regex la fiecare raport).
    suma_plata = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    mentiuni = models.TextField(max_length=50000, null=True, blank=True)
    fisier = models.FileField(max_length=100_000, upload_to=get_save_path)
    actualizat_la = models.DateTimeField(auto_now_add=True)

    @property
    def document_pentru_anul(self):
        return self.data_document.year if self.data_document else None

    @staticmethod
    def total_plati_la_stat():
        total = DocumenteModel.objects.filter(
            tip_document=TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE
        ).aggregate(total=Sum("suma_plata"))["total"]
        return rotund2(D(total or 0))

    class Meta:
        app_label = "documente"
        verbose_name_plural = "Documente"

    def __str__(self):
        return f"{self.tip_document} {self.mentiuni} {self.actualizat_la.isoformat()}"


# Compatibilitate: parserii au fost mutati in services, dar raman importabili
# de aici (teste / cod extern).
from .services import pdf_parser, recipisa_parser  # noqa: F401
