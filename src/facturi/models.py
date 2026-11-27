import datetime
import re

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from fpdf_table import Align, PDFTable
from unidecode import unidecode

from core.settings import get_font_path
from utils.decimale import D, format_suma, rotund2, suma
from utils.files import get_save_path
from utils.localitati import Localitati
from utils.models import UserOwnedModel, UserScopedManager
from utils.valuta import TipTranzactie, Valuta
from utils.views import one_month_from_now


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
    FACTURA_ITALIANA = "factura-italiana", _("Factura in italiana")
    FACTURA_DANEZA = "factura-daneza", _("Factura in daneza")
    FACTURA_OLANDEZA = "factura-olandeza", _("Factura in olandeza")
    FACTURA_SUEDEZA = "factura-suedeza", _("Factura in suedeza")
    FACTURA_FINLANDEZA = "factura-finlandeza", _("Factura in finlandeza")
    # FACTURA_POLONEZA = "factura-poloneza", _("Factura in poloneza")
    # FACTURA_CEHA = "factura-ceha", _("Factura in ceha")
    # FACTURA_MAGHIARA = "factura-maghiara", _("Factura in maghiara")
    # FACTURA_GREACA = "factura-greaca", _("Factura in greaca")
    # FACTURA_BULGARA = "factura-bulgara", _("Factura in bulgara")
    # FACTURA_CROATA = "factura-croata", _("Factura in croata")
    # FACTURA_PORTUGHEZA = "factura-portugheza", _("Factura in portugheza")


factura_romana_pdf = {
    "header_factura": "FACTURA",
    "header_date_factura": ["Serie", "Numar", "Data factura", "Data scadenta"],
    "header_date_client_furnizor": ["Detalii", "Furnizor", "Client"],
    "nume_lang": "Nume",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa",
    "email_lang": "Email",
    "telefon_lang": "Telefon",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt.",
        "Denumire produse sau servicii",
        "U.M.",
        "Cantitate",
        "Pret unitar fara T.V.A.",
        "Valoarea",
    ],
    "header_total_de_plata": "Total de plata:",
}


factura_engleza_pdf = {
    "header_factura": "FACTURA/INVOICE",
    "header_date_factura": [
        "Serie/Series",
        "Numar/Number",
        "Data factura/Invoice Date",
        "Data scadenta/Due Date",
    ],
    "header_date_client_furnizor": ["Detalii/Details", "Furnizor/Supplier", "Client"],
    "nume_lang": "Nume/Name",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Address",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Phone",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Name of products or services",
        "U.M./Unit",
        "Cantitate/Quantity",
        "Pret unitar fara T.V.A./Unit price without VAT",
        "Valoarea/Value",
    ],
    "header_total_de_plata": "Total de plata/Total amount:",
}


factura_germana_pdf = {
    "header_factura": "FACTURA/RECHNUNG",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Nummer",
        "Data factura/Rechnungsdatum",
        "Data scadenta/Fälligkeitsdatum",
    ],
    "header_date_client_furnizor": [
        "Detalii/Details",
        "Furnizor/Lieferant",
        "Client/Kunde",
    ],
    "nume_lang": "Nume/Name",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Adresse",
    "email_lang": "Email",
    "telefon_lang": "Telefon",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./Nr.",
        "Denumire produse sau servicii/Name der Produkte oder Dienstleistungen",
        "U.M./Unit",
        "Cantitate/Menge",
        "Pret unitar fara T.V.A./Stückpreis ohne MwSt.",
        "Valoarea/Wert",
    ],
    "header_total_de_plata": "Total de plata/Gesamt zu zahlen:",
}

factura_franceza_pdf = {
    "header_factura": "FACTURA/FACTURE",
    "header_date_factura": [
        "Serie/Série",
        "Numar/Numéro",
        "Data factura/Date de facture",
        "Data scadenta/Date d'échéance",
    ],
    "header_date_client_furnizor": [
        "Detalii/Détails",
        "Furnizor/Fournisseur",
        "Client",
    ],
    "nume_lang": "Nume/Nom",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Adresse",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Téléphone",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Nom des produits ou services",
        "U.M./Unité",
        "Cantitate/Quantité",
        "Pret unitar fara T.V.A./Prix unitaire hors TVA",
        "Valoarea/Valeur",
    ],
    "header_total_de_plata": "Total de plata/Total à payer:",
}


factura_spaniola_pdf = {
    "header_factura": "FACTURA",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Número",
        "Data factura/Fecha de factura",
        "Data scadenta/Fecha de vencimiento",
    ],
    "header_date_client_furnizor": [
        "Detalii/Detalles",
        "Furnizor/Proveedor",
        "Client/Cliente",
    ],
    "nume_lang": "Nume/Nombre",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Dirección",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Teléfono",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Nombre de productos o servicios",
        "U.M./Unidad",
        "Cantitate/Cantidad",
        "Pret unitar fara T.V.A./Precio unitario sin IVA",
        "Valoarea/Valor",
    ],
    "header_total_de_plata": "Total de plata/Total a pagar:",
}


factura_italiana_pdf = {
    "header_factura": "FACTURA/FATTURA",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Numero",
        "Data factura/Data della fattura",
        "Data scadenta/Data di scadenza",
    ],
    "header_date_client_furnizor": [
        "Detalii/Dettagli",
        "Furnizor/Fornitore",
        "Client/Cliente",
    ],
    "nume_lang": "Nume/Nome",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Indirizzo",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Telefono",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Nome dei prodotti o servizi",
        "U.M./Unità",
        "Cantitate/Quantità",
        "Pret unitar fara T.V.A./Prezzo unitario senza IVA",
        "Valoarea/Valore",
    ],
    "header_total_de_plata": "Total de plata/Total a pagare:",
}


factura_daneza_pdf = {
    "header_factura": "FACTURA/FAKTURA",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Numero",
        "Data factura/Fakturadato",
        "Data scadenta/Forfaldsdato",
    ],
    "header_date_client_furnizor": [
        "Detalii/Detaljer",
        "Furnizor/Leverandør",
        "Client/Kunde",
    ],
    "nume_lang": "Nume/Navn",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Adresse",
    "email_lang": "Email",
    "telefon_lang": "Telefon",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./Nr.",
        "Denumire produse sau servicii/Produkt- eller servicenames",
        "U.M./Enhed",
        "Cantitate/Mængde",
        "Pret unitar fara T.V.A./Enhedspris uden moms",
        "Valoarea/Værdi",
    ],
    "header_total_de_plata": "Total de plata/Total at betale:",
}


factura_olandeza_pdf = {
    "header_factura": "FACTURA/FACTUUR",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Nummer",
        "Data factura/Factuurdatum",
        "Data scadenta/Vervaldatum",
    ],
    "header_date_client_furnizor": [
        "Detalii/Details",
        "Furnizor/Leverancier",
        "Client/Klant",
    ],
    "nume_lang": "Nume",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Adres",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Telefoon",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Naam van de producten of diensten",
        "U.M./Meeteenheid",
        "Cantitate/Hoeveelheid",
        "Pret unitar fara T.V.A./Eenheidsprijs zonder BTW.",
        "Valoarea/Waarde",
    ],
    "header_total_de_plata": "Total de plata/Totale betaling:",
}


factura_suedeza_pdf = {
    "header_factura": "FACTURA/FAKTURA",
    "header_date_factura": [
        "Serie/Serie",
        "Numar/Nummer",
        "Data factura/Datum för faktura",
        "Data scadenta/Utgångsdatum",
    ],
    "header_date_client_furnizor": [
        "Detalii/Detaljer",
        "Furnizor/Familjeförsörjare",
        "Client/Kund",
    ],
    "nume_lang": "Nume/Namn",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Adress",
    "email_lang": "Email",
    "telefon_lang": "Telefon",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Namn på produkter eller tjänster",
        "U.M./Måttenhet",
        "Cantitate/Kvantitet",
        "Pret unitar fara T.V.A./Enhetspris utan moms.",
        "Valoarea/Värde",
    ],
    "header_total_de_plata": "Total de plata/Total betalning:",
}

factura_finlandeza_pdf = {
    "header_factura": "FACTURA/LASKU",
    "header_date_factura": [
        "Serie/Sarja",
        "Numar/Numero",
        "Data factura/Laskun päivämäärä",
        "Data scadenta/Vanhentumispäivä",
    ],
    "header_date_client_furnizor": [
        "Detalii/Tiedot",
        "Furnizor/Toimittaja",
        "Client/Asiakas",
    ],
    "nume_lang": "Nume/Nimi",
    "nr_reg_com_lang": "Nr.Reg.Com.",
    "cif_lang": "CUI/CIF/VAT",
    "adresa_lang": "Adresa/Osoite",
    "email_lang": "Email",
    "telefon_lang": "Telefon/Puhelin",
    "iban_lang": "IBAN",
    "header_produse_servicii": [
        "Nr.Crt./No.",
        "Denumire produse sau servicii/Tuotteiden tai palveluiden nimet",
        "U.M./Mittayksikkö",
        "Cantitate/Määrä",
        "Pret unitar fara T.V.A./Yksikköhinta ilman arvonlisäveroa.",
        "Valoarea/Arvo",
    ],
    "header_total_de_plata": "Total de plata/Maksu yhteensä:",
}


pdf_template_mapper = {
    "e-factura": lambda data: {**data, **factura_romana_pdf},
    "factura-romana": lambda data: {**data, **factura_romana_pdf},
    "factura-engleza": lambda data: {**data, **factura_engleza_pdf},
    "factura-germana": lambda data: {**data, **factura_germana_pdf},
    "factura-franceza": lambda data: {**data, **factura_franceza_pdf},
    "factura-spaniola": lambda data: {**data, **factura_spaniola_pdf},
    "factura-italiana": lambda data: {**data, **factura_italiana_pdf},
    "factura-daneza": lambda data: {**data, **factura_daneza_pdf},
    "factura-olandeza": lambda data: {**data, **factura_olandeza_pdf},
    "factura-suedeza": lambda data: {**data, **factura_suedeza_pdf},
    "factura-finlandeza": lambda data: {**data, **factura_finlandeza_pdf},
}


def creeaza_factura_pdf(data: dict, pdf_output_path: str):

    data = pdf_template_mapper[data["tip_factura"]](data)

    pdf = PDFTable()

    pdf.add_fonts_custom(
        font_name="arial",
        font_extension="ttf",
        font_dir=get_font_path(),
        set_default=True,
    )

    # Date identificare factura
    pdf.table_header([data["header_factura"]], align=Align.L)
    pdf.table_row([""])

    width_cols = pdf.table_cols(2, 2, 4, 4)
    pdf.table_header(data["header_date_factura"], width_cols, align=Align.L)
    pdf.table_row(
        [data["serie"], data["numar"], data["data_emitere"], data["data_scadenta"]],
        width_cols,
    )
    pdf.table_row([""])

    # Date client/furnizor
    pdf.table_header(data["header_date_client_furnizor"], align=Align.L)

    contact_info = [
        [data["nume_lang"] or "", data["nume_furnizor"] or "", data["nume_client"]],
        [
            data["nr_reg_com_lang"] or "",
            data["nr_reg_com_furnizor"] or "",
            data["nr_reg_com_client"] or "",
        ],
        [data["cif_lang"] or "", data["cif_furnizor"] or "", data["cif_client"] or ""],
        [
            data["adresa_lang"] or "",
            data["adresa_furnizor"] or "",
            data["adresa_client"] or "",
        ],
        [
            data["email_lang"] or "",
            data["email_furnizor"] or "",
            data["email_client"] or "",
        ],
        [
            data["telefon_lang"] or "",
            data["telefon_furnizor"] or "",
            data["telefon_client"] or "",
        ],
        [
            data["iban_lang"] or "",
            data["iban_furnizor"] or "",
            data["iban_client"] or "",
        ],
    ]

    for ci in contact_info:
        pdf.table_row(ci, width_list=[30, 80, 80], option="responsive")

    pdf.table_row([""])

    # Produse sau servicii
    width_cols = pdf.table_cols(1, 4, 1, 2, 2, 2)
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)
    pdf.table_row(data["header_produse_servicii"], width_cols, option="responsive")
    pdf.set_font(pdf.font, "", pdf.text_normal_size)

    for ps in data["produse_sau_servicii"]:
        psrow = [
            ps["id"],
            ps["nume_produs_sau_serviciu"],
            ps["cod_unitate"],
            format_suma(ps["numar_unitati"]),
            format_suma(ps["pret_pe_unitate"]),
            format_suma(ps["subtotal"]),
        ]
        pdf.table_row(psrow, width_cols, option="responsive")

    # Total si nota
    if data["nota"]:
        pdf.table_row([f"Note/Obs.: {data['nota']}"])
    else:
        pdf.table_row([""])

    total_text = (
        f"{data['header_total_de_plata']} "
        f"{format_suma(data['total_de_plata'])} {data['valuta']}"
    )
    pdf.table_header([total_text], align=Align.R)

    pdf.output(pdf_output_path)

    return pdf_output_path


def _data_scadenta_default():
    return one_month_from_now().date()


class LinieFactura(models.Model):
    """O linie dintr-o factura (inlocuieste JSON-ul produse_sau_servicii)."""

    factura = models.ForeignKey(
        "FacturaModel", related_name="linii", on_delete=models.CASCADE
    )
    nume = models.CharField(max_length=300)
    cod_unitate = models.CharField(max_length=10, default="HUR")
    cantitate = models.DecimalField(max_digits=14, decimal_places=4, default=1)
    pret_unitar = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        ordering = ["id"]

    @property
    def subtotal(self):
        return rotund2(D(self.cantitate) * D(self.pret_unitar))

    def __str__(self):
        return f"{self.nume} ({self.cantitate} x {self.pret_unitar})"


class FacturaModel(UserOwnedModel):
    serie = models.CharField(max_length=20)
    numar = models.IntegerField()
    data_emitere = models.DateField(default=datetime.date.today)
    data_scadenta = models.DateField(default=_data_scadenta_default)
    tip_factura = models.CharField(
        max_length=30,
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
    client_ue = models.BooleanField(default=False, verbose_name="Client UE")
    email = models.EmailField(max_length=250, null=True, blank=True)
    telefon = models.CharField(max_length=250, null=True, blank=True)
    # Plata: aceeasi enumerare cu incasarile (nu mai avem codurile 42/10).
    tip_tranzactie = models.CharField(
        max_length=10, choices=TipTranzactie, default=TipTranzactie.BANCAR
    )
    valuta = models.CharField(max_length=3, choices=Valuta, default=Valuta.RON)
    nota = models.TextField(max_length=5000, null=True, blank=True)
    data_inserarii = models.DateTimeField(default=timezone.now, null=True, blank=True)

    # Fisierele se genereaza la creare, in serviciul `facturi.generare`.
    fisier_efactura_xml = models.FileField(
        max_length=100_000, upload_to=get_save_path, null=True, blank=True
    )
    fisier_factura_pdf = models.FileField(
        max_length=100_000, upload_to=get_save_path, null=True, blank=True
    )

    objects = UserScopedManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["serie", "numar"],
                name="unique_serie_numar",
                condition=models.Q(user__isnull=True),
            ),
            models.UniqueConstraint(
                fields=["user", "serie", "numar"],
                name="unique_serie_numar_per_user",
                condition=models.Q(user__isnull=False),
            ),
        ]

    @property
    def total_de_plata(self):
        return rotund2(suma(l.subtotal for l in self.linii.all()))

    @property
    def produse_sau_servicii(self):
        """Compatibil cu efactura.xml si cu `creeaza_factura_pdf`."""
        return [
            {
                "id": str(l.id),
                "nume_produs_sau_serviciu": l.nume,
                "cod_unitate": l.cod_unitate,
                "numar_unitati": format_suma(l.cantitate),
                "pret_pe_unitate": format_suma(l.pret_unitar),
                "subtotal": format_suma(l.subtotal),
            }
            for l in self.linii.all()
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

        if localitate.startswith("RO-B,"):
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
        if isinstance(entry, int):
            return entry
        if entry is None:
            return ""
        entry = re.sub(r"\s{2,}", " ", unidecode(entry))
        return entry.upper().strip()

    def save(self, *args, **kwargs):
        self.serie = self.serie.strip().upper()
        self.adresa = self.clean_entry(self.adresa)
        self.nume = self.clean_entry(self.nume)
        self.cif = self.clean_entry(self.cif)
        self.nr_reg_com = self.clean_entry(self.nr_reg_com)
        self.email = self.clean_entry(self.email).lower()
        self.telefon = self.clean_entry(self.telefon)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.serie}-{self.numar} {self.nume} {self.total_de_plata}"
