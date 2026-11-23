import re
from datetime import datetime

import xmltodict
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from pypdf import PdfReader  # https://pypdf.readthedocs.io/en/stable/index.html

from utils.files import get_save_path


# Plafonul TVA de 395000 RON pe an
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

    # Pentru PFA-uri cu cod special de TVA intracomunitar (art. 317):
    # D301 - decont special de TVA (achizitii servicii UE/non-UE, taxare inversa)
    # D390 VIES - declaratie recapitulativa (doar operatiuni intracomunitare UE)
    DECLARATIE_TVA_DECONT_SPECIAL_301 = "Declaratie decont special TVA 301", _(
        "Declaratie decont special TVA 301"
    )
    DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA = (
        "Declaratie decont special TVA 301 recipisa",
        _("Declaratie decont special TVA 301 recipisa"),
    )
    DECLARATIE_TVA_RECAPITULATIVA_390 = "Declaratie recapitulativa TVA 390", _(
        "Declaratie recapitulativa TVA 390"
    )
    DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA = (
        "Declaratie recapitulativa TVA 390 recipisa",
        _("Declaratie recapitulativa TVA 390 recipisa"),
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
        max_length=300, choices=TipDocument, default=TipDocument.DOCUMENT_UTIL
    )
    document_pentru_anul = models.IntegerField(
        null=True, blank=True, validators=[validate_year]
    )
    mentiuni = models.TextField(max_length=50000, null=True, blank=True)
    fisier = models.FileField(max_length=100_000, upload_to=get_save_path)
    actualizat_la = models.DateTimeField(auto_now_add=True)
    parse_tip_document = models.BooleanField(null=True, blank=True, default=True)

    @staticmethod
    def total_plati_la_stat():
        results = DocumenteModel.objects.filter(
            tip_document=TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE,
        )

        platite = 0
        for r in results:
            plata_match = re.search(r"Plata spv ([\d.,]+) RON", r.mentiuni or "")
            if plata_match:
                try:
                    platite += float(plata_match.group(1).replace(",", "."))
                except ValueError:
                    pass

        return round(platite, 2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.parse_tip_document:
            if self.fisier.path.endswith(".pdf"):
                # Recipisele D301/D390 se detecteaza automat din text
                # (tip declaratie, perioada, CIF, index incarcare).
                recipisa = recipisa_parser(self.fisier.path)
                if recipisa:
                    self.tip_document = recipisa["tip_document"]
                    if not self.document_pentru_anul:
                        self.document_pentru_anul = recipisa["anul"]
                    if not self.mentiuni:
                        self.mentiuni = recipisa["mentiuni"]
                    super().save(
                        update_fields=["tip_document", "document_pentru_anul", "mentiuni"]
                    )
                    return

            if self.fisier.path.endswith(".pdf") and self.tip_document in [
                TipDocument.DECLARATIE_UNICA_212.value,
                TipDocument.DECLARATIE_UNICA_212_DOVADA_INCARCARE.value,
                TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value,
            ]:
                data = pdf_parser(self.fisier.path)
                if data:
                    if not self.tip_document:
                        self.tip_document = data["tip_document"]
                    if not self.document_pentru_anul:
                        self.document_pentru_anul = data["document_pentru_anul"]
                    if self.tip_document == TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value and not self.mentiuni:
                        self.mentiuni = f'Plata spv {data["suma_plata_anaf"]} RON'

                super().save(
                    update_fields=["document_pentru_anul", "tip_document", "mentiuni"]
                )

    class Meta:
        app_label = "documente"
        verbose_name_plural = "Documente"

    def __str__(self):
        return f"{self.tip_document} {self.mentiuni} {self.actualizat_la.isoformat()}"


def recipisa_parser(pdf_path: str):
    """Parseaza recipisa ANAF pentru D301/D390.
    Text de referinta: 'Index încărcare: 1296415962 din 10.11.2026 ...
    Aţi depus o declaraţie tip D301 cu numărul de înregistrare INTERNT-...
    pentru perioada de raportare 10 2026 pentru CIF: 52937756'."""
    reader = PdfReader(pdf_path)
    pdf_text = reader.pages[0].extract_text() or ""

    tip_match = re.search(r"declara[ţt]ie\s+tip\s+(D301|D390)", pdf_text, re.IGNORECASE)
    if not tip_match:
        return None

    tip = tip_match.group(1).upper()
    perioada_match = re.search(r"perioada de raportare\s+(\d{1,2})\s+(\d{4})", pdf_text)
    cif_match = re.search(r"CIF:\s*(\d+)", pdf_text)
    index_match = re.search(r"Index\s+[îi]nc[ăa]rcare:\s*(\d+)\s+din\s+(\d\d\.\d\d\.\d\d\d\d)", pdf_text)

    anul = int(perioada_match.group(2)) if perioada_match else None
    luna = int(perioada_match.group(1)) if perioada_match else None
    cif = cif_match.group(1) if cif_match else None

    mentiuni = f"Recipisa {tip}"
    if luna and anul:
        mentiuni += f" perioada {luna:02d}/{anul}"
    if cif:
        mentiuni += f" CIF {cif}"
    if index_match:
        mentiuni += f" index incarcare {index_match.group(1)} din {index_match.group(2)}"
    if "Nu există erori de validare" in pdf_text or "Nu exista erori de validare" in pdf_text:
        mentiuni += " - fara erori de validare"

    return {
        "tip_document": (
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value
            if tip == "D301"
            else TipDocument.DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA.value
        ),
        "tip_declaratie": tip,
        "anul": anul,
        "luna": luna,
        "cif": cif,
        "mentiuni": mentiuni,
    }


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



