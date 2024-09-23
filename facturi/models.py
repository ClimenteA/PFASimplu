import os
import re
from unidecode import unidecode
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from utils.views import one_month_from_now
from utils.localitati import Localitati
from utils.files import get_save_path
from utils.valuta import Valuta
from setari.models import SetariModel
from utils.pdf_from_html import create_pdf_from_html
from core.settings import MEDIA_ROOT


class ModalitatePlata(models.TextChoices):
    BANCAR = "42", _("💳 BANCAR")
    NUMERAR = "10", _("💵 NUMERAR")


class TipFactura(models.TextChoices):
    E_FACTURA = "e-factura", _("E-Factura")
    FACTURA_ROMANA = "factura-romana", _("Factura in romana")
    FACTURA_ENGLEZA = "factura-engleza", _("Factura in engleza")
    FACTURA_GERMANA = "factura-germana", _("Factura in germana")
    FACTURA_FRANCEZA = "factura-franceza", _("Factura in franceza")
    FACTURA_SPANIOLA = "factura-spaniola", _("Factura in spaniola")


class FacturaModel(models.Model):
    serie = models.CharField(max_length=20)
    numar = models.IntegerField()
    data_emitere = models.DateTimeField(default=timezone.now)
    data_scadenta = models.DateTimeField(default=one_month_from_now)
    tip_factura = models.CharField(
        max_length=300,
        choices=TipFactura,
        default=TipFactura.E_FACTURA,
    )
    # Client
    nume = models.CharField(max_length=200)
    cif = models.CharField(max_length=50)
    nr_reg_com = models.CharField(max_length=50, null=True, blank=True)
    localitate = models.CharField(
        max_length=250,
        choices=Localitati,
        null=True,
        blank=True,
        default=Localitati.LOCALITATE_GENERIC,
    )
    adresa = models.CharField(max_length=1000)
    email = models.EmailField(max_length=250, null=True, blank=True)
    telefon = models.CharField(max_length=250, null=True, blank=True)
    # Plata
    tip_tranzactie = models.CharField(
        max_length=250, choices=ModalitatePlata, default=ModalitatePlata.BANCAR
    )
    total_de_plata = models.FloatField()
    valuta = models.CharField(max_length=3, choices=Valuta, default=Valuta.RON)
    # Produse sau servicii
    # id, numar_unitati, total_de_plata, nume_produs_sau_serviciu, cod_unitate, pret_pe_unitate, subtotal
    produse_sau_servicii = models.JSONField(default=list)
    nota = models.TextField(max_length=5000, null=True, blank=True)
    data_inserarii = models.DateTimeField(default=timezone.now, null=True, blank=True)

    # Fisiere
    fisier_efactura_xml = models.FileField(
        max_length=100_000, upload_to=get_save_path, null=True, blank=True
    )
    fisier_factura_pdf = models.FileField(
        max_length=100_000, upload_to=get_save_path, null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["serie", "numar"], name="unique_serie_numar"
            )
        ]

    @staticmethod
    def get_cod_judet(localitate: str):
        if not localitate:
            return Localitati.LOCALITATE_GENERIC.value
        return localitate.split(",")[0].strip()

    @staticmethod
    def get_localitate(localitate: str):

        if not localitate:
            return Localitati.LOCALITATE_GENERIC.value

        if localitate.startswith("RO-B"):
            return localitate.split("Bucuresti,")[1].strip().upper().replace(" ", "")

        loc = ""

        judet = re.search(r"RO.*, jud. (.*?),", localitate)
        if judet:
            judet = judet.group(1)

        comuna = re.search(r"RO.*, jud. .*, com. (.*?),", localitate)
        if comuna:
            comuna = comuna.group(1)

        oras_sat = re.search(r"RO.*, jud. .*, (.*)", localitate)
        if oras_sat:
            oras_sat = oras_sat.group(1)

        if judet == comuna or judet == oras_sat:
            loc = judet
        else:
            loc += judet if judet else " "
            loc += comuna if comuna else " "
            loc += oras_sat if oras_sat else " "

        if not loc:
            return Localitati.LOCALITATE_GENERIC.value

        return re.sub(r"\s{2,}", "", loc.strip().capitalize())

    @staticmethod
    def clean_entry(entry: str | None):
        if entry is None:
            return ""
        entry = re.sub(r"\s{2,}", " ", unidecode(entry))
        return entry.upper().strip()

    def save(self, *args, **kwargs):
        furnizor = SetariModel.objects.first()

        self.serie = self.serie.strip().upper()
        self.adresa = self.clean_entry(self.adresa)
        self.nume = self.clean_entry(self.nume)
        self.cif = self.clean_entry(self.cif)
        self.nr_reg_com = self.clean_entry(self.nr_reg_com)
        self.email = self.clean_entry(self.email).lower()
        self.telefon = self.clean_entry(self.telefon)

        show_iban_furnizor = self.tip_tranzactie == ModalitatePlata.BANCAR.value

        context = {
            "tip_factura": self.tip_factura,
            "valuta": self.valuta,
            "show_iban_furnizor": show_iban_furnizor,
            "serie": self.serie,
            "numar": self.numar,
            "serie_numar": f"{self.serie}-{self.numar}",
            "data_emitere": self.data_emitere.date().isoformat(),
            "data_scadenta": self.data_scadenta.date().isoformat(),
            "nota": self.nota,
            "adresa_furnizor": furnizor.adresa,
            "localitate_furnizor": self.get_localitate(furnizor.localitate),
            "cod_judet_furnizor": self.get_cod_judet(furnizor.localitate),
            "cif_furnizor": furnizor.cif,
            "nr_reg_com_furnizor": furnizor.nr_reg_com,
            "nume_furnizor": furnizor.nume,
            "email_furnizor": furnizor.email,
            "telefon_furnizor": furnizor.telefon,
            "iban_furnizor": furnizor.iban,
            "adresa_client": self.adresa,
            "localitate_client": self.get_localitate(self.localitate),
            "cod_judet_client": self.get_cod_judet(self.localitate),
            "nume_client": self.nume,
            "cif_client": self.cif,
            "nr_reg_com_client": self.nr_reg_com,
            "email_client": self.email,
            "telefon_client": self.telefon,
            "cod_modalitate_plata": self.tip_tranzactie,
            "total_de_plata": self.total_de_plata,
            "produse_sau_servicii": self.produse_sau_servicii,
        }

        if self.tip_factura == TipFactura.E_FACTURA.value:
            xml_content = render_to_string("efactura.xml", context)
            self.fisier_efactura_xml.save(
                "efactura.xml", ContentFile(xml_content), save=False
            )

        factura_content = render_to_string("factura_pdf.html", context)
        save_pdf_path = os.path.join(MEDIA_ROOT, "factura_invoice.pdf")
        save_pdf_path = create_pdf_from_html(factura_content, save_pdf_path)
        with open(save_pdf_path, "rb") as pdf:
            self.fisier_factura_pdf.save(
                "factura_invoice.pdf", ContentFile(pdf.read()), save=False
            )

        super().save(*args, **kwargs)
