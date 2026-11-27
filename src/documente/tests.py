"""Teste pentru integrarea D301/D390 + Jurnal de cumparari + plata TVA.

Cazurile de referinta sunt exemplele reale din stocare/completare-declaratii-tva:
- Cortecs GmbH (Austria, UE): 21 EUR x 5.3 = 111.30 lei baza, TVA 23.37 lei;
- Google Cloud EMEA (Irlanda, UE): 50 USD x 4.5 = 225 lei baza, TVA 47.25 lei;
- Cloudflare/Kilo Code (SUA, non-UE): doar D301 sectiunea 4, CIF normal.

Declaratiile se descarca din pagina Cheltuieli (filtru pe luna + Descarca):
- UE: D301 + D390 pe codul special de TVA intracomunitar (art. 317);
- non-UE: doar D301 pe CIF-ul normal din Setari.
"""

import datetime
import os
import tempfile
from unittest.mock import patch
from zipfile import ZipFile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cheltuieli.models import CheltuialaModel, Deductibilitate, TipAchizitie
from documente.models import DocumenteModel, TipDocument
from documente.services import recipisa_parser
from setari.models import SetariModel
from utils.decimale import D
from utils.tari import este_tara_ue
from utils.trezorerie import get_judet_din_localitate, get_link_iban_trezorerie
from utils.tva import (
    calculeaza_d301,
    calculeaza_d301_lista,
    calculeaza_d390,
    calculeaza_jurnal_cumparari,
    get_luni_cu_taxare_inversa,
    termen_depunere,
)
from utils.tva_documente import genereaza_pachet_tva

# Cursuri BNR fixe pentru teste (nu cerem reteaua).
CURSURI_TEST = {
    "2026-09-01": {"USD": 4.5, "EUR": 5.0},
    "2026-09-14": {"USD": 4.5316, "EUR": 5.0},
    "2026-09-18": {"USD": 4.55, "EUR": 5.0},
    "2026-09-19": {"USD": 4.5839, "EUR": 5.0},
    "2026-09-24": {"USD": 4.6, "EUR": 5.0},
    "2026-09-25": {"USD": 4.6395, "EUR": 5.0},
    "2026-09-30": {"USD": 4.6, "EUR": 5.0},
    "2026-10-01": {"EUR": 5.3, "USD": 4.6},
    "2026-10-02": {"EUR": 5.3447, "USD": 4.6},
}


USER_TEST = None


def login_test_client(testcase):
    """Autentifica clientul de test si seteaza utilizatorul pentru fixtures."""
    global USER_TEST
    from django.contrib.auth.models import User

    USER_TEST, _ = User.objects.get_or_create(username="test@pfasimplu.ro")
    testcase.user = USER_TEST
    testcase.client.force_login(USER_TEST)


def mock_get_bnr_rates(dateValue):
    return CURSURI_TEST


def pdf_recipisa_d301() -> bytes:
    """Recipisa D301 sintetica pentru teste (PDF-urile reale sunt in stocare/,
    exclusa din git prin .gitignore, deci nu e disponibila intr-un checkout curat)."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for linie in (
        "Declaratie tip D301",
        "perioada de raportare 10 2026",
        "CIF: 52937756",
        "Index incarcare: 1296415962 din 13.10.2026",
        "Nu exista erori de validare",
    ):
        pdf.cell(0, 9, linie, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def creeaza_setari(**kwargs):
    defaults = {
        "user": USER_TEST,
        "nume": "CLIMENTE ALIN IONEL PERSOANA FIZICA AUTORIZATA",
        "localitate": "RO-IS, jud. Iasi, Iasi",
        "adresa": "str. SOS. PRINCIPALA, nr. 162, bl. A7, sc. A, ap. 9, jud. IASI",
        "nr_reg_com": "F22/123/2020",
        "cif": "43000098",
        "email": "test@example.com",
        "caen_principal": "6201",
        "cod_tva_intracomunitar": "52937756",
        "cont_iban_trezoreria": "RO41TREZ40620A100101XTVA",
    }
    defaults.update(kwargs)
    return SetariModel.objects.create(**defaults)


def creeaza_cheltuiala_ue(**kwargs):
    """Factura Cortecs (Austria): 21 EUR, 02.10.2026."""
    defaults = {
        "user": USER_TEST,
        "nume_cheltuiala": "Top-up AI inference Cortecs",
        "suma": 21.0,
        "valuta": "EUR",
        "tip_tranzactie": "BANCAR",
        "data_inserarii": datetime.date(2026, 10, 2),
        "tip_achizitie": TipAchizitie.SERVICII_UE,
        "furnizor_denumire": "CORTECS GMBH",
        "furnizor_cod_fiscal": "ATU77164426",
        "furnizor_tara": "AT",
        "numar_factura": "PBW-2026-003576",
        "data_facturii": datetime.date(2026, 10, 2),
        "fisier": SimpleUploadedFile(
            "factura.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    }
    defaults.update(kwargs)
    return CheltuialaModel.objects.create(**defaults)


def creeaza_cheltuiala_non_ue(**kwargs):
    """Factura Cloudflare (SUA): 21 USD, 19.09.2026."""
    defaults = {
        "user": USER_TEST,
        "nume_cheltuiala": "Cloudflare subscription",
        "suma": 21.0,
        "valuta": "USD",
        "tip_tranzactie": "BANCAR",
        "data_inserarii": datetime.date(2026, 9, 19),
        "tip_achizitie": TipAchizitie.SERVICII_NON_UE,
        "furnizor_denumire": "CLOUDFLARE INC",
        "furnizor_cod_fiscal": "27-0805829",
        "furnizor_tara": "US",
        "numar_factura": "IN-79973856",
        "data_facturii": datetime.date(2026, 9, 19),
        "fisier": SimpleUploadedFile(
            "factura.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    }
    defaults.update(kwargs)
    return CheltuialaModel.objects.create(**defaults)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class TaxareInversaCheltuialaTests(TestCase):
    def setUp(self):
        login_test_client(self)

    """Calculele automate la salvare pe cheltuiala (cazul Cortecs)."""

    def test_calcul_automat_ue(self, _mock):
        c = creeaza_cheltuiala_ue()
        self.assertEqual(c.curs_bnr_aplicat, D("5.3"))
        self.assertEqual(c.baza_in_lei, D("111.3"))
        self.assertEqual(c.baza_in_lei, c.suma_in_ron)
        self.assertEqual(c.tva_autolichidata, D("23.373"))

    def test_tva_adaugata_la_deducere(self, _mock):
        c = creeaza_cheltuiala_ue()
        # TVA autolichidata este cheltuiala deductibila a PFA-ului (art. 317):
        # deducerea = suma_in_ron (cursul zilei bancare anterioare: 21 x 5.3)
        #            + TVA autolichidat (111.3 x 0.21 = 23.373)
        self.assertEqual(c.deducere_in_ron, D("134.673"))

    def test_cheltuiala_romania_neschimbata(self, _mock):
        c = CheltuialaModel.objects.create(
            user=USER_TEST,
            nume_cheltuiala="Consumabile",
            suma=100.0,
            valuta="RON",
            data_inserarii=datetime.date(2026, 10, 2),
            fisier=SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
        )
        self.assertIsNone(c.tva_autolichidata)
        self.assertIsNone(c.baza_in_lei)
        self.assertEqual(c.deducere_in_ron, D("100.0"))
        self.assertEqual(c.tip_achizitie, TipAchizitie.ROMANIA)

    def test_ue_non_ue_dedus_din_tara(self, _mock):
        # Utilizatorul alege gresit "non-UE" pentru Austria -> corectat automat
        c = creeaza_cheltuiala_ue(tip_achizitie=TipAchizitie.SERVICII_NON_UE)
        self.assertEqual(c.tip_achizitie, TipAchizitie.SERVICII_UE)
        # UK este non-UE dupa Brexit
        c2 = creeaza_cheltuiala_non_ue(
            furnizor_tara="GB",
            tip_achizitie=TipAchizitie.SERVICII_UE,
            numar_factura="UK-1",
        )
        self.assertEqual(c2.tip_achizitie, TipAchizitie.SERVICII_NON_UE)

    def test_validare_cod_tva_lipsa_ue(self, _mock):
        with self.assertRaises(ValidationError):
            creeaza_cheltuiala_ue(furnizor_cod_fiscal="")

    def test_validare_prefix_tara_gresit(self, _mock):
        with self.assertRaises(ValidationError):
            creeaza_cheltuiala_ue(furnizor_cod_fiscal="DE123456789")

    def test_validare_numar_factura_lipsa(self, _mock):
        with self.assertRaises(ValidationError):
            creeaza_cheltuiala_ue(numar_factura="")

    def test_curs_bnr_recalculat_la_editare(self, _mock):
        # Cursul este o valoare derivata: se recalculeaza din suma si data,
        # nu poate fi suprascris manual (e @property, fara setter).
        c = creeaza_cheltuiala_ue()
        c.suma = 42.0
        c.save()
        self.assertEqual(c.curs_bnr_aplicat, D("5.3"))
        self.assertEqual(c.baza_in_lei, D("42.0") * D("5.3"))

    def test_curs_din_data_inserarii_independent_de_data_facturii(self, _mock):
        c = creeaza_cheltuiala_ue(data_facturii=None)
        self.assertEqual(c.curs_bnr_aplicat, D("5.3"))
        self.assertEqual(c.baza_in_lei, c.suma_in_ron)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class CalculDeclaratiiTests(TestCase):
    """Agregarea lunara D301/D390/jurnal, pe exemplele reale."""

    def setUp(self):
        login_test_client(self)
        self.setari = creeaza_setari()

    def test_d301_ue_cortecs(self, _mock):
        creeaza_cheltuiala_ue()
        d301 = calculeaza_d301(2026, 10, self.setari)
        self.assertIsNotNone(d301)
        # Codul special de TVA intracomunitar, nu CIF-ul normal
        self.assertEqual(d301["cif"], "52937756")
        self.assertEqual(d301["baza4"], D("111.3"))
        self.assertEqual(d301["tva4"], D("23.37"))
        # Factura UE apare si in sectiunea 4 si in 4.1 (tip_operatie 5)
        self.assertEqual(d301["baza5"], D("111.3"))
        self.assertEqual(d301["tva5"], D("23.37"))
        tipuri = [r["tip_operatie"] for r in d301["randuri"]]
        self.assertEqual(tipuri, ["4", "5"])
        self.assertEqual(d301["total_de_plata"], D("23.37"))
        self.assertEqual(d301["termen"], datetime.date(2026, 11, 25))

    def test_d301_non_ue_doar_sectiunea_4(self, _mock):
        creeaza_cheltuiala_non_ue()
        d301 = calculeaza_d301(2026, 9, self.setari)
        self.assertIsNotNone(d301)
        # Non-UE se declara pe CIF-ul normal din Setari, nu pe codul special art. 317.
        self.assertEqual(d301["cif"], "43000098")
        # 21 x 4.55 = 95.55 (cursul zilei bancare anterioare inserarii)
        self.assertEqual(d301["baza4"], D("95.55"))
        self.assertEqual(d301["baza5"], 0)
        self.assertEqual(d301["tva5"], 0)
        tipuri = [r["tip_operatie"] for r in d301["randuri"]]
        self.assertEqual(tipuri, ["4"])

    def test_d301_non_ue_fara_cod_special_foloseste_cif_normal(self, _mock):
        setari_fara_cod = creeaza_setari(cod_tva_intracomunitar=None)
        creeaza_cheltuiala_non_ue()
        d301 = calculeaza_d301(2026, 9, setari_fara_cod)
        self.assertEqual(d301["cif"], "43000098")

    def test_d390_doar_ue(self, _mock):
        creeaza_cheltuiala_non_ue()
        self.assertIsNone(calculeaza_d390(2026, 9, self.setari))

        creeaza_cheltuiala_ue()
        d390 = calculeaza_d390(2026, 10, self.setari)
        self.assertIsNotNone(d390)
        self.assertEqual(d390["cif"], "52937756")
        self.assertEqual(d390["nr_operatori"], 1)
        # Baza D390 rotunjita la intreg: 111.3 -> 111
        self.assertEqual(d390["bazaS"], 111)
        rand = d390["randuri"][0]
        self.assertEqual(rand["tip"], "S")
        self.assertEqual(rand["tara"], "AT")
        # Cod operator fara prefixul de tara
        self.assertEqual(rand["cod_operator"], "U77164426")
        self.assertEqual(rand["denumire_operator"], "CORTECS GMBH")

    def test_d390_grupare_pe_operator(self, _mock):
        creeaza_cheltuiala_ue()
        creeaza_cheltuiala_ue(numar_factura="PBW-2026-003999", suma=10.0)
        d390 = calculeaza_d390(2026, 10, self.setari)
        self.assertEqual(d390["nr_operatori"], 1)
        # 111.3 + 53 = 164.3 -> 164
        self.assertEqual(d390["bazaS"], 164)

    def test_luna_mixta_ue_si_non_ue(self, _mock):
        # Septembrie: Google (UE, 50 USD) + Cloudflare + Kilo (non-UE).
        # Cu coduri diferite (special art. 317 vs CIF) rezulta doua D301.
        creeaza_cheltuiala_ue(
            furnizor_denumire="GOOGLE CLOUD EMEA LIMITED",
            furnizor_cod_fiscal="IE3668997OH",
            furnizor_tara="IE",
            numar_factura="5687406092",
            suma=50.0,
            valuta="USD",
            data_inserarii=datetime.date(2026, 9, 14),
            data_facturii=datetime.date(2026, 9, 14),
        )
        creeaza_cheltuiala_non_ue()
        creeaza_cheltuiala_non_ue(
            furnizor_denumire="KILO CODE",
            numar_factura="XD0OYRZT-0003",
            suma=50.0,
            data_inserarii=datetime.date(2026, 9, 25),
            data_facturii=datetime.date(2026, 9, 25),
        )

        d301_lista = calculeaza_d301_lista(2026, 9, self.setari)
        # Luna mixta cu coduri diferite: doua D301 separate, fiecare pe codul ei.
        self.assertEqual(len(d301_lista), 2)
        d301_ue, d301_non = d301_lista
        self.assertEqual(d301_ue["cif"], "52937756")
        self.assertEqual(d301_non["cif"], "43000098")
        # Google (UE): sectiunea 4 + sectiunea 4.1
        self.assertEqual(d301_ue["baza4"], D("225"))
        self.assertEqual(d301_ue["baza5"], D("225"))
        # Cloudflare + Kilo (non-UE): doar sectiunea 4
        self.assertEqual(d301_non["baza4"], D("323.05"))
        self.assertEqual(d301_non["baza5"], 0)

        d301 = calculeaza_d301(2026, 9, self.setari)
        self.assertEqual(d301["baza4"], D("225"))
        self.assertEqual(
            len([r for r in d301["randuri"] if r["tip_operatie"] == "4"]), 1
        )
        self.assertEqual(
            len([r for r in d301["randuri"] if r["tip_operatie"] == "5"]), 1
        )

        d390 = calculeaza_d390(2026, 9, self.setari)
        self.assertEqual(d390["nr_operatori"], 1)
        self.assertEqual(d390["randuri"][0]["cod_operator"], "3668997OH")
        self.assertEqual(d390["bazaS"], 225)

    def test_luna_mixta_fara_cod_special_o_singura_d301(self, _mock):
        # Fara cod special art. 317, ambele tipuri se declara pe CIF: o singura D301.
        setari_fara_cod = creeaza_setari(cod_tva_intracomunitar=None)
        creeaza_cheltuiala_ue(
            data_inserarii=datetime.date(2026, 9, 14),
            data_facturii=datetime.date(2026, 9, 14),
        )
        creeaza_cheltuiala_non_ue()
        d301_lista = calculeaza_d301_lista(2026, 9, setari_fara_cod)
        self.assertEqual(len(d301_lista), 1)
        self.assertEqual(d301_lista[0]["cif"], "43000098")
        self.assertEqual(
            len([r for r in d301_lista[0]["randuri"] if r["tip_operatie"] == "4"]), 2
        )
        self.assertEqual(
            len([r for r in d301_lista[0]["randuri"] if r["tip_operatie"] == "5"]), 1
        )

    def test_jurnal_cumparari(self, _mock):
        creeaza_cheltuiala_ue()
        jurnal = calculeaza_jurnal_cumparari(2026, 10)
        self.assertIsNotNone(jurnal)
        rand = jurnal["randuri"][0]
        self.assertEqual(rand["cod_referinta"], "15-16")
        self.assertEqual(rand["furnizor_cod_fiscal"], "ATU77164426")
        self.assertEqual(rand["baza"], D("111.3"))
        self.assertEqual(rand["tva"], D("23.37"))
        self.assertEqual(rand["total_document"], D("134.67"))
        self.assertEqual(jurnal["total_tva"], D("23.37"))

    def test_luna_fara_operatiuni(self, _mock):
        self.assertIsNone(calculeaza_d301(2026, 1, self.setari))
        self.assertIsNone(calculeaza_d390(2026, 1, self.setari))
        self.assertIsNone(calculeaza_jurnal_cumparari(2026, 1))
        self.assertEqual(get_luni_cu_taxare_inversa(2026), [])

    def test_luni_cu_taxare_inversa(self, _mock):
        creeaza_cheltuiala_ue()
        creeaza_cheltuiala_non_ue()
        self.assertEqual(get_luni_cu_taxare_inversa(2026), [9, 10])

    def test_termen_depunere_decembrie(self, _mock):
        self.assertEqual(termen_depunere(2026, 12), datetime.date(2027, 1, 25))
        self.assertEqual(termen_depunere(2026, 10), datetime.date(2026, 11, 25))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class GenerareDocumenteTests(TestCase):
    """Zip-ul generat: declaratii Markdown grupate in foldere pe CIF/cod TVA."""

    def setUp(self):
        login_test_client(self)
        self.setari = creeaza_setari()

    def test_pachet_zip_complet(self, _mock):
        creeaza_cheltuiala_ue()
        pachet = genereaza_pachet_tva(2026, 10, self.setari)
        self.assertIsNotNone(pachet)
        with ZipFile(pachet["zip_path"]) as zf:
            names = zf.namelist()
        # Folder cu prefix TVA pentru codul TVA intracomunitar.
        self.assertIn("TVA-52937756/D301_2026_10.md", names)
        self.assertIn("TVA-52937756/D390_2026_10.md", names)
        self.assertIn("TVA-52937756/Jurnal_cumparari_2026_10.xlsx", names)
        # Factura furnizorului atasata cheltuielii, inclusa in folder.
        self.assertIn("TVA-52937756/facturi/factura.pdf", names)
        # Fara XML-uri si fara PDF-uri generate (doar factura atasata).
        self.assertFalse(any(n.endswith(".xml") for n in names))

    def test_jurnal_xlsx_grupat_pe_cod(self, _mock):
        import io

        import pandas as pd

        creeaza_cheltuiala_ue()
        creeaza_cheltuiala_non_ue(
            data_inserarii=datetime.date(2026, 10, 19),
            data_facturii=datetime.date(2026, 10, 19),
        )
        pachet = genereaza_pachet_tva(2026, 10, self.setari)
        with ZipFile(pachet["zip_path"]) as zf:
            # Fiecare folder are jurnalul doar cu facturile declarate pe codul lui.
            df_ue = pd.read_excel(
                io.BytesIO(zf.read("TVA-52937756/Jurnal_cumparari_2026_10.xlsx"))
            )
            df_non = pd.read_excel(
                io.BytesIO(zf.read("CIF-43000098/Jurnal_cumparari_2026_10.xlsx"))
            )
        self.assertEqual(df_ue["Document Numar"].tolist(), ["PBW-2026-003576"])
        self.assertEqual(df_non["Document Numar"].tolist(), ["IN-79973856"])
        self.assertTrue((df_ue["Referinta cod"] == "15-16").all())
        self.assertTrue((df_non["Referinta cod"] == "15-16").all())

    def test_d301_md_completat(self, _mock):
        from utils.tva_documente import genereaza_d301_md

        creeaza_cheltuiala_ue()
        d301 = calculeaza_d301(2026, 10, self.setari)
        md = genereaza_d301_md(d301, self.setari)
        self.assertIn("D301 - Decont special de TVA - octombrie 2026", md)
        self.assertIn("`RO52937756`", md)
        self.assertIn("art. 317", md)
        # Factura apare si in sectiunea 4 si in sectiunea 4.1
        self.assertEqual(md.count("PBW-2026-003576"), 2)
        self.assertIn("5,3", md)
        self.assertIn("111,3", md)
        self.assertIn("23,373", md)
        self.assertIn("23,37", md)  # totalul rotunjit la 2 zecimale
        self.assertIn("25.11.2026", md)
        # Instructiunea de plata la trezorerie
        self.assertIn("RO41TREZ40620A100101XTVA", md)
        self.assertIn("20A100101", md)
        # Cum se depune: cont SPV pe codul intracomunitar, e-guvernare + certificat
        self.assertIn("cont SPV", md)
        self.assertIn("https://www.e-guvernare.ro/", md)
        self.assertIn("DEPUNERE DECLARATII ANAF", md)
        self.assertIn("https://decl.anaf.mfinante.gov.ro/my.policy", md)
        self.assertIn("Authentificare cu certificat", md)

    def test_d301_md_non_ue_pe_cif(self, _mock):
        from utils.tva_documente import genereaza_d301_md

        creeaza_cheltuiala_non_ue()
        d301 = calculeaza_d301(2026, 9, self.setari)
        md = genereaza_d301_md(d301, self.setari)
        self.assertIn("`RO43000098`", md)
        self.assertIn("codul normal de PFA (CIF)", md)
        self.assertIn("IN-79973856", md)
        # Sectiunea 4.1 ramane zero pentru non-UE
        self.assertIn("**Zero**", md)
        self.assertNotIn("U77164426", md)

    def test_d390_md_completat(self, _mock):
        from utils.tva_documente import genereaza_d390_md

        creeaza_cheltuiala_ue()
        d390 = calculeaza_d390(2026, 10, self.setari)
        md = genereaza_d390_md(d390, self.setari)
        self.assertIn("D390 VIES - Declarație recapitulativă - octombrie 2026", md)
        self.assertIn("`RO52937756`", md)
        self.assertIn("`Austria-AT`", md)
        self.assertIn("`U77164426`", md)
        self.assertIn("`CORTECS GMBH`", md)
        self.assertIn("**`111`**", md)
        self.assertIn("25.11.2026", md)

    def test_pachet_non_ue_fara_d390(self, _mock):
        creeaza_cheltuiala_non_ue()
        pachet = genereaza_pachet_tva(2026, 9, self.setari)
        with ZipFile(pachet["zip_path"]) as zf:
            names = zf.namelist()
        self.assertIn("CIF-43000098/D301_2026_09.md", names)
        self.assertIn("CIF-43000098/facturi/factura.pdf", names)
        self.assertNotIn("CIF-43000098/D390_2026_09.md", names)
        self.assertFalse(any("D390" in n for n in names))
        # Non-UE se declara pe CIF-ul normal
        self.assertEqual(pachet["d301"]["cif"], "43000098")

    def test_pachet_luna_mixta_doua_d301(self, _mock):
        # UE pe codul special art. 317 + non-UE pe CIF: cate un folder pe cod.
        creeaza_cheltuiala_ue(
            data_inserarii=datetime.date(2026, 9, 14),
            data_facturii=datetime.date(2026, 9, 14),
        )
        creeaza_cheltuiala_non_ue()
        pachet = genereaza_pachet_tva(2026, 9, self.setari)
        with ZipFile(pachet["zip_path"]) as zf:
            names = zf.namelist()
        self.assertIn("TVA-52937756/D301_2026_09.md", names)
        self.assertIn("TVA-52937756/D390_2026_09.md", names)
        self.assertIn("TVA-52937756/Jurnal_cumparari_2026_09.xlsx", names)
        self.assertIn("CIF-43000098/D301_2026_09.md", names)
        self.assertIn("CIF-43000098/Jurnal_cumparari_2026_09.xlsx", names)
        # D390 doar in folderul codului intracomunitar (UE).
        self.assertNotIn("CIF-43000098/D390_2026_09.md", names)
        coduri = [d["cif"] for d in pachet["d301_lista"]]
        self.assertEqual(coduri, ["52937756", "43000098"])

    def test_pachet_luna_goala(self, _mock):
        self.assertIsNone(genereaza_pachet_tva(2026, 1, self.setari))


class RecipisaParserTests(TestCase):
    def setUp(self):
        login_test_client(self)

    """Parsarea recipiselor D301/D390 (text real din exemplele depuse)."""

    RECIPISA_D301 = """MINISTERUL FINANŢELOR
AGENŢIA NAŢIONALĂ DE ADMINISTRARE FISCALĂ

Index încărcare: 1296415962 din 10.11.2026
Aţi depus o declaraţie tip D301  cu numărul de înregistrare INTERNT-1296415962-2026 din data de
10.11.2026 pentru perioada de raportare 10 2026  pentru CIF: 52937756

Nu există erori de validare.
"""

    def _creeaza_pdf_cu_text(self, text):
        from fpdf import FPDF

        from core.settings import get_font_path

        pdf = FPDF()
        pdf.add_font("arial", "", os.path.join(get_font_path(), "arial.ttf"))
        pdf.add_page()
        pdf.set_font("arial", size=10)
        for line in text.split("\n"):
            pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
        path = os.path.join(tempfile.mkdtemp(), "recipisa.pdf")
        pdf.output(path)
        return path

    def test_recipisa_d301(self):
        path = self._creeaza_pdf_cu_text(self.RECIPISA_D301)
        data = recipisa_parser(path)
        self.assertIsNotNone(data)
        self.assertEqual(data["tip_declaratie"], "D301")
        self.assertEqual(data["anul"], 2026)
        self.assertEqual(data["luna"], 10)
        self.assertEqual(data["cif"], "52937756")
        self.assertEqual(
            data["tip_document"],
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value,
        )
        self.assertIn("1296415962", data["mentiuni"])

    def test_recipisa_d390(self):
        text = self.RECIPISA_D301.replace("D301", "D390").replace(
            "1296415962", "1296475983"
        )
        path = self._creeaza_pdf_cu_text(text)
        data = recipisa_parser(path)
        self.assertEqual(data["tip_declaratie"], "D390")
        self.assertEqual(
            data["tip_document"],
            TipDocument.DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA.value,
        )

    def test_pdf_obisnuit_nu_e_recipisa(self):
        path = self._creeaza_pdf_cu_text("Factura simpla fara declaratii.")
        self.assertIsNone(recipisa_parser(path))


class SetariTVAFieldsTests(TestCase):
    def setUp(self):
        login_test_client(self)

    def test_iban_trezorerie_valid(self):
        s = creeaza_setari()
        self.assertEqual(s.cont_iban_trezoreria, "RO41TREZ40620A100101XTVA")

    def test_iban_trezorerie_invalid_form(self):
        from setari.forms import SetariForm

        form = SetariForm(
            data={
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cont_iban_trezoreria": "RO00TREZ40620A100101XTVA",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cont_iban_trezoreria", form.errors)

    def test_cif_pentru_achizitie(self):
        s = creeaza_setari()
        self.assertEqual(s.get_cif_pentru_achizitie(este_ue=True), "52937756")
        self.assertEqual(s.get_cif_pentru_achizitie(este_ue=False), "43000098")
        s.cod_tva_intracomunitar = "RO52937756"
        self.assertEqual(s.get_cif_pentru_achizitie(este_ue=True), "52937756")

    def test_link_trezorerie_din_localitate(self):
        self.assertEqual(get_judet_din_localitate("RO-IS, jud. Iasi, Iasi"), "Iasi")
        # Localitate cu trezorerie cunoscuta -> link direct la PDF-ul ANAF (sursa IBAN-ului)
        self.assertIn(
            "iban_TREZ405_TREZ406.pdf",
            get_link_iban_trezorerie("RO-IS, jud. Iasi, Iasi"),
        )
        # Localitate fara trezorerie operativa proprie -> pagina judetului
        self.assertIn(
            "Iasi.htm",
            get_link_iban_trezorerie("RO-IS, jud. Iasi, com. Todiresti, Boldesti"),
        )
        self.assertIn(
            "Satu_Mare.htm",
            get_link_iban_trezorerie("RO-SM, jud. Satu Mare, com. X, Y"),
        )
        self.assertIn(
            "Caras_Severin.htm",
            get_link_iban_trezorerie("RO-CS, jud. Caras-Severin, com. X, Y"),
        )

    def test_tari_ue_non_ue(self):
        self.assertTrue(este_tara_ue("AT"))
        self.assertTrue(este_tara_ue("IE"))
        self.assertFalse(este_tara_ue("US"))
        self.assertFalse(este_tara_ue("GB"))  # Brexit
        self.assertFalse(este_tara_ue(""))


class IbanTrezorerieAutoTests(TestCase):
    def setUp(self):
        login_test_client(self)

    """IBAN-ul trezoreriei se deduce automat din localitatea selectata in Setari
    (date extrase din sursele oficiale ANAF - static/iban_trezorerie.json)."""

    def test_iban_iasi(self):
        from utils.trezorerie import get_iban_trezorerie_pentru_localitate

        r = get_iban_trezorerie_pentru_localitate("RO-IS, jud. Iasi, Iasi")
        self.assertIsNotNone(r)
        self.assertEqual(r["iban"], "RO41TREZ40620A100101XTVA")
        self.assertEqual(r["cod_trezorerie"], "TREZ406")
        self.assertIn("iban_TREZ405_TREZ406.pdf", r["sursa"])

    def test_iban_pascani(self):
        from utils.trezorerie import get_iban_trezorerie_pentru_localitate

        r = get_iban_trezorerie_pentru_localitate("RO-IS, jud. Iasi, Pascani")
        self.assertEqual(r["iban"], "RO63TREZ40720A100101XTVA")

    def test_iban_bucuresti_sectoare(self):
        from utils.trezorerie import get_iban_trezorerie_pentru_localitate

        r1 = get_iban_trezorerie_pentru_localitate("RO-B, jud. Bucuresti, Sector 1")
        r6 = get_iban_trezorerie_pentru_localitate("RO-B, jud. Bucuresti, Sector 6")
        self.assertIn("TREZ701", r1["iban"])
        self.assertIn("TREZ706", r6["iban"])
        self.assertNotEqual(r1["iban"], r6["iban"])

    def test_iban_variante_nume(self):
        from utils.trezorerie import get_iban_trezorerie_pentru_localitate

        # Abrevieri ANAF: Sf. / Tg., articulare: Simleul/Simleu, Otelul/Otelu
        cazuri = [
            ("RO-CV, jud. Covasna, com. Sfantul Gheorghe, Sfantu Gheorghe", "TREZ256"),
            ("RO-CV, jud. Covasna, com. Tirgu Secuiesc, Targu Secuiesc", "TREZ257"),
            ("RO-SJ, jud. Salaj, Simleu Silvaniei", "TREZ563"),
            ("RO-CS, jud. Caras-Severin, Otelu Rosu", "TREZ188"),
            ("RO-NT, jud. Neamt, com. Piatra Neamt, Piatra-Neamt", "TREZ491"),
            ("RO-GJ, jud. Gorj, com. Tirgu Carbunesti, Carbunesti", "TREZ337"),
            ("RO-CT, jud. Constanta, com. Eforie, Eforie Nord", "TREZ236"),
        ]
        for localitate, cod_trez in cazuri:
            r = get_iban_trezorerie_pentru_localitate(localitate)
            self.assertIsNotNone(r, localitate)
            self.assertIn(cod_trez, r["iban"], localitate)

    def test_fara_potriviri_gresite(self):
        from utils.trezorerie import get_iban_trezorerie_pentru_localitate

        # Sate fara trezorerie proprie NU trebuie sa primeasca IBAN-ul
        # unui oras doar pentru ca impart un cuvant din nume.
        cazuri = [
            "RO-MM, jud. Maramures, Boiu Mare",  # nu Baia Mare
            "RO-HR, jud. Harghita, Cristuru Secuiesc",  # nu Odorheiu Secuiesc
            "RO-AB, jud. Alba, com. Bucium, Valea Alba",  # nu Alba Iulia
            "RO-IS, jud. Iasi, com. Todiresti, Boldesti",
        ]
        for localitate in cazuri:
            self.assertIsNone(
                get_iban_trezorerie_pentru_localitate(localitate), localitate
            )

    def test_toate_ibanurile_valid_mod97(self):
        import json
        import os

        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "iban_trezorerie.json"
        )
        with open(path, encoding="utf-8") as f:
            date = json.load(f)
        self.assertGreaterEqual(len(date["trezorerii"]), 200)
        for t in date["trezorerii"]:
            iban = t["iban"]
            self.assertEqual(len(iban), 24, iban)
            self.assertIn("20A100101", iban)
            rearr = iban[4:] + iban[:4]
            numeric = "".join(str(int(c, 36)) for c in rearr)
            self.assertEqual(int(numeric) % 97, 1, iban)

    def test_endpoint_iban_trezorerie(self):
        from django.urls import reverse

        r = self.client.get(
            reverse("setari-iban-trezorerie"),
            {"localitate": "RO-IS, jud. Iasi, Iasi"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["iban"], "RO41TREZ40620A100101XTVA")
        self.assertIn("pdf", data["sursa"])
        self.assertEqual(data["cod_bugetar"], "20A100101")

        # Localitate fara trezorerie -> iban null, dar link de verificare
        r = self.client.get(
            reverse("setari-iban-trezorerie"),
            {"localitate": "RO-IS, jud. Iasi, com. Todiresti, Boldesti"},
        )
        data = r.json()
        self.assertIsNone(data["iban"])
        self.assertIn("Iasi.htm", data["sursa"])

    def test_salvare_completeaza_iban_automat(self):
        """Bug fix: la 'Salveaza datele PFA' cu IBAN trezorerie gol,
        acesta se completeaza automat din localitate (server-side)."""
        from django.urls import reverse

        self.client.post(
            reverse("setari"),
            {
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cod_tva_intracomunitar": "",
                "cont_iban_trezoreria": "",
            },
        )
        s = SetariModel.objects.first()
        self.assertEqual(s.cont_iban_trezoreria, "RO41TREZ40620A100101XTVA")

    def test_salvare_pastreaza_iban_manual(self):
        """IBAN-ul introdus manual nu se suprascrie la salvare."""
        from django.urls import reverse

        self.client.post(
            reverse("setari"),
            {
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cod_tva_intracomunitar": "",
                "cont_iban_trezoreria": "RO63TREZ40720A100101XTVA",  # Pascani, manual
            },
        )
        s = SetariModel.objects.first()
        self.assertEqual(s.cont_iban_trezoreria, "RO63TREZ40720A100101XTVA")

    @patch("utils.trezorerie._get_trezorerii")
    @patch("utils.scrape_iban_trezorerie.scrape")
    @patch("utils.scrape_iban_trezorerie.salveaza_json")
    def test_salvare_ruleaza_scraper_daca_json_lipseste(
        self, mock_salveaza, mock_scrape, mock_cache
    ):
        """Daca iban_trezorerie.json lipseste, la salvarea Setarilor se ruleaza
        automat scraper-ul ANAF si IBAN-ul se completeaza din datele proaspete."""
        from django.urls import reverse

        randuri_proaspete = [
            {
                "judet": "Iasi",
                "cod_trezorerie": "TREZ406",
                "nume_trezorerie": "Trezorerie operativa Municipiul Iasi",
                "localitate": "iasi",
                "iban": "RO41TREZ40620A100101XTVA",
                "cod_bugetar": "20A100101",
                "sursa": "https://static.anaf.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/iban_TREZ405_TREZ406.pdf",
            }
        ]
        mock_scrape.return_value = randuri_proaspete
        # Prima verificare: tabel gol -> scrape; dupa salvare: date disponibile.
        # itertools.chain: dupa primele 2 apeluri, tot datele proaspete.
        import itertools

        mock_cache.side_effect = itertools.chain(
            [[], randuri_proaspete], itertools.repeat(randuri_proaspete)
        )

        response = self.client.post(
            reverse("setari"),
            {
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cod_tva_intracomunitar": "",
                "cont_iban_trezoreria": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_scrape.assert_called_once()
        mock_salveaza.assert_called_once_with(randuri_proaspete)

        s = SetariModel.objects.first()
        self.assertEqual(s.cont_iban_trezoreria, "RO41TREZ40620A100101XTVA")

    @patch("utils.trezorerie._get_trezorerii", return_value=[])
    @patch("utils.scrape_iban_trezorerie.scrape", side_effect=Exception("lipsa retea"))
    def test_salvare_esueaza_scraping_continua(self, mock_scrape, _mock_cache):
        """Daca scraper-ul esueaza (lipsa retea), salvarea Setarilor continua
        cu avertisment, fara IBAN automat."""
        from django.urls import reverse

        response = self.client.post(
            reverse("setari"),
            {
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cod_tva_intracomunitar": "",
                "cont_iban_trezoreria": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        s = SetariModel.objects.first()
        self.assertIsNotNone(s)  # setarile s-au salvat
        self.assertIsNone(s.cont_iban_trezoreria)
        mesajele = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("Nu am putut descarca" in m for m in mesajele))

    @patch("utils.scrape_iban_trezorerie.scrape")
    def test_scraper_nu_ruleaza_daca_json_exista(self, mock_scrape):
        """Cu tabelul deja disponibil, scraper-ul NU se ruleaza la salvare."""
        from django.urls import reverse

        self.client.post(
            reverse("setari"),
            {
                "nume": "TEST PFA",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "str. Test",
                "nr_reg_com": "F1",
                "cif": "123",
                "email": "t@t.ro",
                "caen_principal": "6201",
                "conturi_iban": "[]",
                "cod_tva_intracomunitar": "",
                "cont_iban_trezoreria": "",
            },
        )
        mock_scrape.assert_not_called()
        s = SetariModel.objects.first()
        self.assertEqual(s.cont_iban_trezoreria, "RO41TREZ40620A100101XTVA")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class FluxCheltuieliTVATests(TestCase):
    """Fluxul prin pagina Cheltuieli: filtru pe luni + Descarca declaratiile TVA."""

    def setUp(self):
        login_test_client(self)
        self.setari = creeaza_setari()

    def test_descarca_zip_pentru_luna(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("cheltuieli-tva-descarca"), {"anul": 2026, "luna": 10}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("D301-D390_2026_10.zip", response["Content-Disposition"])

    def test_descarca_luna_goala_redirect(self, _mock):
        response = self.client.get(
            reverse("cheltuieli-tva-descarca"), {"anul": 2026, "luna": 1}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cheltuieli/")

    def test_descarca_fara_setari_redirect(self, _mock):
        SetariModel.objects.all().delete()
        creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("cheltuieli-tva-descarca"), {"anul": 2026, "luna": 10}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/setari/")

    def test_pagina_documente_fara_tabel_tva(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(reverse("documente"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Declarații TVA")
        self.assertNotContains(response, "tva/genereaza")

    def test_filtru_extern_pe_luna(self, _mock):
        creeaza_cheltuiala_ue()  # octombrie, UE
        creeaza_cheltuiala_non_ue()  # septembrie, non-UE
        CheltuialaModel.objects.create(
            user=USER_TEST,
            nume_cheltuiala="Consumabile",
            suma=100.0,
            valuta="RON",
            data_inserarii=datetime.date(2026, 10, 2),
            fisier=SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
        )
        response = self.client.get(
            reverse("cheltuieli"), {"extern": 1, "anul_extern": 2026, "luna_extern": 10}
        )
        self.assertEqual(response.status_code, 200)
        items = list(response.context["page_items"])
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].este_ue)
        self.assertEqual(response.context["luni_extern"], [9, 10])
        self.assertContains(response, "Descarca")
        self.assertNotContains(response, "Consumabile")

    def test_recipisa_detectata_la_incarcare(self, _mock):
        upload = SimpleUploadedFile(
            "recipisa.pdf", pdf_recipisa_d301(), content_type="application/pdf"
        )

        response = self.client.post(
            reverse("documente"),
            {
                "tip_document": TipDocument.DOCUMENT_UTIL,
                "mentiuni": "",
                "fisier": upload,
                "parse_tip_document": True,
            },
        )
        self.assertEqual(response.status_code, 302)

        doc = DocumenteModel.objects.latest("id")
        self.assertEqual(
            doc.tip_document,
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value,
        )
        self.assertEqual(doc.document_pentru_anul, 2026)
        self.assertIn("10/2026", doc.mentiuni)
        self.assertIn("52937756", doc.mentiuni)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class JurnalCumparariRegistreTests(TestCase):
    def setUp(self):
        login_test_client(self)
        self.setari = creeaza_setari()

    def test_descarca_jurnal_csv(self, _mock):
        cheltuiala = creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("descarca-jurnal-cumparari"),
            {"filetype": "CSV", "anul": 2026, "luna": 10},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("PBW-2026-003576", content)
        self.assertIn("15-16", content)
        self.assertIn("134.67", content)
        # Coloana cu fisierul documentului justificativ, per rand.
        self.assertIn("Document justificativ (fisier)", content)
        self.assertIn(os.path.basename(cheltuiala.fisier.path), content)

    def test_jurnal_gol_redirect(self, _mock):
        response = self.client.get(
            reverse("descarca-jurnal-cumparari"), {"filetype": "CSV", "anul": 2026}
        )
        self.assertEqual(response.status_code, 302)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class CheltuieliFormularViewTests(TestCase):
    """Fluxul prin formularul de cheltuieli: precompletare minima, calcule automate."""

    def setUp(self):
        login_test_client(self)
        self.setari = creeaza_setari()

    def test_post_cheltuiala_ue_calculeaza_automat(self, _mock):
        upload = SimpleUploadedFile(
            "factura.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        )
        response = self.client.post(
            reverse("cheltuieli"),
            {
                "nume_cheltuiala": "Cortecs AI",
                "deductibila": Deductibilitate.DEDUCTIBILA_INTEGRAL,
                "suma": "21.00",
                "valuta": "EUR",
                "tip_tranzactie": "BANCAR",
                "data_inserarii": "2026-10-02",
                "tip_achizitie": TipAchizitie.SERVICII_UE,
                "furnizor_denumire": "CORTECS GMBH",
                "furnizor_cod_fiscal": "ATU77164426",
                "furnizor_tara": "AT",
                "numar_factura": "PBW-2026-003576",
                "data_facturii": "2026-10-02",
                "fisier": upload,
                "obiect_de_inventar": False,
                "mijloc_fix": False,
                "scos_din_uz": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        c = CheltuialaModel.objects.get(numar_factura="PBW-2026-003576")
        self.assertEqual(c.baza_in_lei, D("111.3"))
        self.assertEqual(c.tva_autolichidata, D("23.373"))
        self.assertEqual(c.curs_bnr_aplicat, D("5.3"))

    def test_typeahead_furnizor(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(reverse("cheltuieli-cauta-furnizor", args=["cort"]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["furnizor_cod_fiscal"], "ATU77164426")
        self.assertEqual(data[0]["furnizor_tara"], "AT")
