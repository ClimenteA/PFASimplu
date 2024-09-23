import re
from datetime import datetime
import xmltodict
from pypdf import PdfReader  # https://pypdf.readthedocs.io/en/stable/index.html
from django.db import models
from django.utils.translation import gettext_lazy as _
from utils.files import get_save_path
from django.core.exceptions import ValidationError


# Plafonul TVA de 300000 RON pe an (cca. 60.000 EUR, 5440 Euro/luna, 31 Eur/Ora) 6 saptamani concediu
# https://virginradio.ro/p-ce-declaratii-trebuie-sa-depuna-un-pfa-in-decursul-unui-an
class TipDocument(models.TextChoices):

    DOCUMENT_UTIL = "Document util", _("Document util")

    # Dovada plata taxe si impozite
    DOVADA_PLATA_TAXE_SI_IMPOZITE = "Dovada plata taxe si impozite", _(
        "Dovada plata taxe si impozite"
    )

    # Declaratia Unica (Declaratie 212) - declarație de venituri și contribuții sociale pentru PFA-uri
    DECLARATIE_UNICA_212 = "Declaratie unica 212", _("Declaratie unica 212")
    DECLARATIE_UNICA_212_DOVADA_INCARCARE = "Declaratie unica 212 dovada incarcare", _(
        "Declaratie unica 212 dovada incarcare"
    )

    # Declarația 097 – Notificare privind aplicarea sistemului TVA la încasare (se inregistreaza o singura data)
    DECLARATIE_INREGISTRARE_SCOP_TVA_097 = (
        "Declaratie inregistrare PFA in scop TVA 097",
        _("Declaratie inregistrare PFA in scop TVA 097"),
    )
    DECLARATIE_INREGISTRARE_SCOP_TVA_097_DOVADA_INCARCARE = (
        "Declaratie inregistrare PFA in scop TVA 097 dovada incarcare",
        _("Declaratie inregistrare PFA in scop TVA 097 dovada incarcare"),
    )

    # Pentru cei care au depasit pragul TVA.
    # Declarația 300 – Declarație privind decontul de taxă pe valoarea adăugată.
    DECLARATIE_TVA_DECONT_300 = "Declaratie decont TVA 300", _(
        "Declaratie decont TVA 300"
    )
    DECLARATIE_TVA_DECONT_300_DOVADA_INCARCARE = (
        "Declaratie decont TVA 300 dovada incarcare",
        _("Declaratie decont TVA 300 dovada incarcare"),
    )

    # Declarațiile 392B și 392A – Declarații informative privind livrările de bunuri, prestări de servicii și achizițiil efectuate în anul precedent
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392A = (
        "Declaratie activitate financiara 392A",
        _("Declaratie activitate financiara 392A"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392A_DOVADA_INCARCARE = (
        "Declaratie activitate financiara 392A dovada incarcare",
        _("Declaratie activitate financiara 392A dovada incarcare"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392B = (
        "Declaratie activitate financiara 392B",
        _("Declaratie activitate financiara 392B"),
    )
    DECLARATIE_TVA_ACTIVITATE_FINANCIARA_392B_DOVADA_INCARCARE = (
        "Declaratie activitate financiara 392B dovada incarcare",
        _("Declaratie activitate financiara 392B dovada incarcare"),
    )

    # Pentru cei care au salariati
    # Declarația 112 – Declarație privind obligațiile de plată a contribuțiilor sociale, impozitului pe venit și evidența nominală a persoanelor asigurate.
    DECLARATIE_OBLIGATI_PLATA_PENTRU_SALARIATI_112 = (
        "Declaratie obligatii de plata pentru salariati 112",
        _("Declaratie obligatii de plata pentru salariati 112"),
    )
    DECLARATIE_OBLIGATI_PLATA_PENTRU_SALARIATI_212_DOVADA_INCARCARE = (
        "Declaratie obligatii de plata pentru salariati 112 dovada incarcare",
        _("Declaratie obligatii de plata pentru salariati 112  dovada incarcare"),
    )


def validate_year(value):
    if value < 2000 or value > 2500:
        raise ValidationError(f"{value} nu este un an valid.")


class DocumenteModel(models.Model):
    tip_document = models.CharField(
        max_length=300, choices=TipDocument, default=TipDocument.DECLARATIE_UNICA_212
    )
    document_pentru_anul = models.IntegerField(
        null=True, blank=True, validators=[validate_year]
    )
    mentiuni = models.TextField(max_length=50000, null=True, blank=True)
    fisier = models.FileField(max_length=100_000, upload_to=get_save_path)
    actualizat_la = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def total_plati_la_stat():
        results = DocumenteModel.objects.filter(
            tip_document=TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE,
        )

        platite = 0
        for r in results:
            plata_match = re.search(r"Plata spv (\d+\.\d+) RON", r.mentiuni)
            if plata_match:
                platite += float(plata_match.group(1))

        return round(platite, 2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.fisier.path.endswith(".pdf") and self.tip_document in [
            TipDocument.DECLARATIE_UNICA_212.value,
            TipDocument.DECLARATIE_UNICA_212_DOVADA_INCARCARE.value,
            TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value,
        ]:
            data = pdf_parser(self.fisier.path)
            if data:
                self.tip_document = data["tip_document"]
                self.document_pentru_anul = data["document_pentru_anul"]
                if self.tip_document == TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value:
                    plata_spv_text = f'Plata spv {data["suma_plata_anaf"]} RON'
                    if plata_spv_text not in self.mentiuni:
                        self.mentiuni = plata_spv_text

                super().save(
                    update_fields=["document_pentru_anul", "tip_document", "mentiuni"]
                )

    class Meta:
        app_label = "documente"
        verbose_name_plural = "Documente"

    def __str__(self):
        return f"{self.tip_document} {self.mentiuni} self.actualizat_la.isoformat()"


def pdf_parser(pdf_path: str):

    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    pdf_text = page.extract_text()

    # D212
    xml = None
    d212_dict = None
    for name, content_list in reader.attachments.items():
        for i, content in enumerate(content_list):
            xml = content.decode("utf-8")
            break
    if xml:
        d212_dict = xmltodict.parse(xml)
        return {
            "tip_document": TipDocument.DECLARATIE_UNICA_212,
            "document_pentru_anul": int(d212_dict["d212"]["@an_r"]),  # '2024'
        }

    # D212 dovada incarcare
    if "D212" in pdf_text or "declaratie unica" in pdf_text:
        data_dovada_incarcare_match = re.search(
            r"Index încărcare: \d{1,} din (\d\d.\d\d.\d\d\d\d)", pdf_text, re.DOTALL
        )
        if data_dovada_incarcare_match:
            return {
                "tip_document": TipDocument.DECLARATIE_UNICA_212_DOVADA_INCARCARE,
                "document_pentru_anul": datetime.strptime(
                    data_dovada_incarcare_match.group(1), "%d.%m.%Y"
                ).year,  # '01.02.2023'
            }

    suma_ghiseul_match = re.search(r"Total valoare: (.*?) Lei", pdf_text, re.DOTALL)
    if suma_ghiseul_match:
        data = re.search(
            r"Data plății:  (\d\d.\d\d.\d\d\d\d) \d\d:\d\d:\d\d", pdf_text
        ).group(
            1
        )  # 19.03.2024
        suma = float(
            suma_ghiseul_match.group(1).replace(".", "").replace(",", ".")
        )  # 18.00,89
        return {
            "tip_document": TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE,
            "document_pentru_anul": datetime.strptime(data, "%d.%m.%Y").year,
            "suma_plata_anaf": suma,
        }
