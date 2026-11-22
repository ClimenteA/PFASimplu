"""Teste pentru integrarea D301/D390 + Jurnal de cumparari + plata TVA.

Cazurile de referinta sunt exemplele reale din stocare/completare-declaratii-tva:
- Cortecs GmbH (Austria, UE): 21 EUR x 5.3447 = 112.24 lei baza, TVA 23.57 lei;
- Google Cloud EMEA (Irlanda, UE): 50 USD x 4.5316 = 226.58 lei baza, TVA 47.58 lei;
- Cloudflare/Kilo Code (SUA, non-UE): doar D301 sectiunea 4, CIF normal.
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
from documente.models import (
    DocumenteModel,
    TipDocument,
    DeclaratieTVAModel,
    TipDeclaratieTVA,
    StatusDeclaratieTVA,
    recipisa_parser,
)
from setari.models import SetariModel
from utils.tari import este_tara_ue
from utils.trezorerie import get_link_iban_trezorerie, get_judet_din_localitate
from utils.tva import (
    calculeaza_d301,
    calculeaza_d390,
    calculeaza_jurnal_cumparari,
    get_luni_cu_taxare_inversa,
    termen_depunere,
)
from utils.tva_documente import (
    genereaza_d301_xml,
    genereaza_d390_xml,
    genereaza_pachet_tva,
)


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


def mock_get_bnr_rates(dateValue):
    return CURSURI_TEST


def creeaza_setari(**kwargs):
    defaults = dict(
        nume="CLIMENTE ALIN IONEL PERSOANA FIZICA AUTORIZATA",
        localitate="RO-IS, jud. Iasi, Iasi",
        adresa="str. SOS. NATIONALA, nr. 182, bl. A2, sc. A, ap. 3, jud. IASI",
        nr_reg_com="F22/123/2020",
        cif="43000098",
        email="test@example.com",
        iban="RO04INGB0000999911194833",
        caen_principal="6201",
        cod_tva_intracomunitar="52937756",
        cont_iban_trezoreria="RO41TREZ40620A100101XTVA",
    )
    defaults.update(kwargs)
    return SetariModel.objects.create(**defaults)


def creeaza_cheltuiala_ue(**kwargs):
    """Factura Cortecs (Austria): 21 EUR, 02.10.2026."""
    defaults = dict(
        nume_cheltuiala="Top-up AI inference Cortecs",
        suma=21.0,
        valuta="EUR",
        tip_tranzactie="BANCAR",
        data_inserarii=datetime.date(2026, 10, 2),
        tip_achizitie=TipAchizitie.SERVICII_UE,
        furnizor_denumire="CORTECS GMBH",
        furnizor_cod_fiscal="ATU77164426",
        furnizor_tara="AT",
        numar_factura="PBW-2026-003576",
        data_facturii=datetime.date(2026, 10, 2),
        fisier=SimpleUploadedFile("factura.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
    )
    defaults.update(kwargs)
    return CheltuialaModel.objects.create(**defaults)


def creeaza_cheltuiala_non_ue(**kwargs):
    """Factura Cloudflare (SUA): 21 USD, 19.09.2026."""
    defaults = dict(
        nume_cheltuiala="Cloudflare subscription",
        suma=21.0,
        valuta="USD",
        tip_tranzactie="BANCAR",
        data_inserarii=datetime.date(2026, 9, 19),
        tip_achizitie=TipAchizitie.SERVICII_NON_UE,
        furnizor_denumire="CLOUDFLARE INC",
        furnizor_cod_fiscal="27-0805829",
        furnizor_tara="US",
        numar_factura="IN-79973856",
        data_facturii=datetime.date(2026, 9, 19),
        fisier=SimpleUploadedFile("factura.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
    )
    defaults.update(kwargs)
    return CheltuialaModel.objects.create(**defaults)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class TaxareInversaCheltuialaTests(TestCase):
    """Calculele automate la salvare pe cheltuiala (cazul Cortecs)."""

    def test_calcul_automat_ue(self, _mock):
        c = creeaza_cheltuiala_ue()
        self.assertEqual(c.curs_bnr_aplicat, 5.3447)
        self.assertEqual(c.baza_in_lei, 112.24)
        self.assertEqual(c.tva_autolichidata, 23.57)

    def test_tva_adaugata_la_deducere(self, _mock):
        c = creeaza_cheltuiala_ue()
        # TVA autolichidata este cheltuiala deductibila a PFA-ului (art. 317):
        # deducerea = suma_in_ron (cursul OMFP al platii) + TVA autolichidat
        self.assertEqual(c.deducere_in_ron, round(c.suma_in_ron + 23.57, 2))

    def test_cheltuiala_romania_neschimbata(self, _mock):
        c = CheltuialaModel.objects.create(
            nume_cheltuiala="Consumabile",
            suma=100.0,
            valuta="RON",
            data_inserarii=datetime.date(2026, 10, 2),
            fisier=SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
        )
        self.assertIsNone(c.tva_autolichidata)
        self.assertIsNone(c.baza_in_lei)
        self.assertEqual(c.deducere_in_ron, 100.0)
        self.assertEqual(c.tip_achizitie, TipAchizitie.ROMANIA)

    def test_ue_non_ue_dedus_din_tara(self, _mock):
        # Utilizatorul alege gresit "non-UE" pentru Austria -> corectat automat
        c = creeaza_cheltuiala_ue(tip_achizitie=TipAchizitie.SERVICII_NON_UE)
        self.assertEqual(c.tip_achizitie, TipAchizitie.SERVICII_UE)
        # UK este non-UE dupa Brexit
        c2 = creeaza_cheltuiala_non_ue(
            furnizor_tara="GB", tip_achizitie=TipAchizitie.SERVICII_UE,
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

    def test_curs_manual_pastrat_la_editare(self, _mock):
        c = creeaza_cheltuiala_ue()
        c.curs_bnr_aplicat = 5.5
        c.save()
        self.assertEqual(c.curs_bnr_aplicat, 5.5)
        self.assertEqual(c.baza_in_lei, round(21.0 * 5.5, 2))

    def test_data_facturii_fallback_pe_data_cheltuielii(self, _mock):
        c = creeaza_cheltuiala_ue(data_facturii=None)
        self.assertEqual(c.curs_bnr_aplicat, 5.3447)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class CalculDeclaratiiTests(TestCase):
    """Agregarea lunara D301/D390/jurnal, pe exemplele reale."""

    def setUp(self):
        self.setari = creeaza_setari()

    def test_d301_ue_cortecs(self, _mock):
        creeaza_cheltuiala_ue()
        d301 = calculeaza_d301(2026, 10, self.setari)
        self.assertIsNotNone(d301)
        # Codul special de TVA intracomunitar, nu CIF-ul normal
        self.assertEqual(d301["cif"], "52937756")
        self.assertEqual(d301["baza4"], 112.24)
        self.assertEqual(d301["tva4"], 23.57)
        # Factura UE apare si in sectiunea 4 si in 4.1 (tip_operatie 5)
        self.assertEqual(d301["baza5"], 112.24)
        self.assertEqual(d301["tva5"], 23.57)
        tipuri = [r["tip_operatie"] for r in d301["randuri"]]
        self.assertEqual(tipuri, ["4", "5"])
        self.assertEqual(d301["total_de_plata"], 23.57)
        self.assertEqual(d301["termen"], datetime.date(2026, 11, 25))

    def test_d301_non_ue_doar_sectiunea_4(self, _mock):
        creeaza_cheltuiala_non_ue()
        d301 = calculeaza_d301(2026, 9, self.setari)
        self.assertIsNotNone(d301)
        # Fara cod special completat, non-UE foloseste CIF-ul normal;
        # aici avem cod special (art. 317) deci declaratia se depune pe el.
        self.assertEqual(d301["cif"], "52937756")
        self.assertEqual(d301["baza4"], round(21.0 * 4.5839, 2))
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
        # Baza D390 rotunjita la intreg: 112.24 -> 112
        self.assertEqual(d390["bazaS"], 112)
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
        # 112.24 + 53.45 = 165.69 -> 166
        self.assertEqual(d390["bazaS"], 166)

    def test_luna_mixta_ue_si_non_ue(self, _mock):
        # Septembrie: Google (UE, 50 USD) + Cloudflare + Kilo (non-UE)
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

        d301 = calculeaza_d301(2026, 9, self.setari)
        # 226.58 + 96.26 + 231.97 = 554.81 (rotunjire half-up la 2 zecimale per factura)
        self.assertEqual(d301["baza4"], 554.81)
        self.assertEqual(d301["baza5"], 226.58)
        self.assertEqual(len([r for r in d301["randuri"] if r["tip_operatie"] == "4"]), 3)
        self.assertEqual(len([r for r in d301["randuri"] if r["tip_operatie"] == "5"]), 1)

        d390 = calculeaza_d390(2026, 9, self.setari)
        self.assertEqual(d390["nr_operatori"], 1)
        self.assertEqual(d390["randuri"][0]["cod_operator"], "3668997OH")
        self.assertEqual(d390["bazaS"], 227)

    def test_jurnal_cumparari(self, _mock):
        creeaza_cheltuiala_ue()
        jurnal = calculeaza_jurnal_cumparari(2026, 10)
        self.assertIsNotNone(jurnal)
        rand = jurnal["randuri"][0]
        self.assertEqual(rand["cod_referinta"], "15-16")
        self.assertEqual(rand["furnizor_cod_fiscal"], "ATU77164426")
        self.assertEqual(rand["baza"], 112.24)
        self.assertEqual(rand["tva"], 23.57)
        self.assertEqual(rand["total_document"], 135.81)
        self.assertEqual(jurnal["total_tva"], 23.57)

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
    """XML-urile ANAF si zip-ul generat."""

    def setUp(self):
        self.setari = creeaza_setari()

    def test_d301_xml_structura_oficiala(self, _mock):
        import xml.etree.ElementTree as ET

        creeaza_cheltuiala_ue()
        d301 = calculeaza_d301(2026, 10, self.setari)
        xml = genereaza_d301_xml(d301, self.setari)
        root = ET.fromstring(xml)
        self.assertTrue(root.tag.endswith("declaratie301"))
        self.assertEqual(root.get("cif"), "52937756")
        self.assertEqual(root.get("pers_inreg"), "2")
        self.assertEqual(root.get("baza4"), "112.24")
        self.assertEqual(root.get("tva4"), "23.57")
        self.assertEqual(root.get("baza5"), "112.24")
        self.assertEqual(root.get("tva5"), "23.57")
        sectiuni = list(root)
        self.assertEqual(len(sectiuni), 2)
        self.assertEqual(sectiuni[0].get("tip_operatie"), "4")
        self.assertEqual(sectiuni[1].get("tip_operatie"), "5")
        self.assertEqual(sectiuni[0].get("nr_doc"), "PBW-2026-003576")
        self.assertEqual(sectiuni[0].get("data_doc"), "02.10.2026")
        self.assertEqual(sectiuni[0].get("curs_valutar"), "5.3447")

    def test_d390_xml_structura_oficiala(self, _mock):
        import xml.etree.ElementTree as ET

        creeaza_cheltuiala_ue()
        d390 = calculeaza_d390(2026, 10, self.setari)
        xml = genereaza_d390_xml(d390, self.setari)
        root = ET.fromstring(xml)
        self.assertTrue(root.tag.endswith("declaratie390"))
        self.assertEqual(root.get("cui"), "52937756")
        self.assertEqual(root.get("luna"), "10")
        rezumat = root.find("{mfp:anaf:dgti:d390:declaratie:v3}rezumat")
        self.assertEqual(rezumat.get("bazaS"), "112")
        self.assertEqual(rezumat.get("nrOPI"), "1")
        operatie = root.find("{mfp:anaf:dgti:d390:declaratie:v3}operatie")
        self.assertEqual(operatie.get("tip"), "S")
        self.assertEqual(operatie.get("tara"), "AT")
        self.assertEqual(operatie.get("codO"), "U77164426")
        self.assertEqual(operatie.get("baza"), "112")

    def test_pachet_zip_complet(self, _mock):
        creeaza_cheltuiala_ue()
        pachet = genereaza_pachet_tva(2026, 10, self.setari)
        self.assertIsNotNone(pachet)
        with ZipFile(pachet["zip_path"]) as zf:
            names = zf.namelist()
        self.assertIn("D301_2026_10.pdf", names)
        self.assertIn("D301_2026_10.xml", names)
        self.assertIn("D390_2026_10.pdf", names)
        self.assertIn("D390_2026_10.xml", names)
        self.assertIn("Jurnal_cumparari_2026_10.pdf", names)
        self.assertIn("Jurnal_cumparari_2026_10.csv", names)
        self.assertIn("Instructiune_plata_TVA_2026_10.pdf", names)

    def test_pachet_non_ue_fara_d390(self, _mock):
        creeaza_cheltuiala_non_ue()
        pachet = genereaza_pachet_tva(2026, 9, self.setari)
        with ZipFile(pachet["zip_path"]) as zf:
            names = zf.namelist()
        self.assertIn("D301_2026_09.pdf", names)
        self.assertNotIn("D390_2026_09.pdf", names)
        self.assertNotIn("D390_2026_09.xml", names)

    def test_pachet_luna_goala(self, _mock):
        self.assertIsNone(genereaza_pachet_tva(2026, 1, self.setari))


class RecipisaParserTests(TestCase):
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
        text = self.RECIPISA_D301.replace("D301", "D390").replace("1296415962", "1296475983")
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

    def test_iban_trezorerie_valid(self):
        s = creeaza_setari()
        self.assertEqual(s.cont_iban_trezoreria, "RO41TREZ40620A100101XTVA")

    def test_iban_trezorerie_invalid_form(self):
        from setari.forms import SetariForm

        form = SetariForm(data={
            "nume": "TEST PFA", "localitate": "RO-IS, jud. Iasi, Iasi",
            "adresa": "str. Test", "nr_reg_com": "F1", "cif": "123",
            "email": "t@t.ro", "caen_principal": "6201",
            "conturi_iban": "[]",
            "cont_iban_trezoreria": "RO00TREZ40620A100101XTVA",
        })
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
        self.assertIn("Iasi.htm", get_link_iban_trezorerie("RO-IS, jud. Iasi, Iasi"))
        self.assertIn("Satu_Mare.htm", get_link_iban_trezorerie("RO-SM, jud. Satu Mare, Satu Mare"))
        self.assertIn("Caras_Severin.htm", get_link_iban_trezorerie("RO-CS, jud. Caras-Severin, Resita"))
        # Fara pagina dedicata -> link generic ANAF
        self.assertNotIn("iban2014/", get_link_iban_trezorerie("RO-B, jud. Bucuresti, Bucuresti"))

    def test_tari_ue_non_ue(self):
        self.assertTrue(este_tara_ue("AT"))
        self.assertTrue(este_tara_ue("IE"))
        self.assertFalse(este_tara_ue("US"))
        self.assertFalse(este_tara_ue("GB"))  # Brexit
        self.assertFalse(este_tara_ue(""))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class FluxDocumenteViewTests(TestCase):
    """Fluxul complet prin view-uri: generare zip, statusuri, marchare plata."""

    def setUp(self):
        self.setari = creeaza_setari()

    def test_genereaza_creeaza_declaratii_si_descarca_zip(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")

        d301 = DeclaratieTVAModel.objects.get(tip=TipDeclaratieTVA.D301, anul=2026, luna=10)
        self.assertEqual(d301.status, StatusDeclaratieTVA.DESCARCATA)
        self.assertEqual(d301.cif_folosit, "52937756")
        self.assertEqual(d301.total_de_plata, 23.57)
        d390 = DeclaratieTVAModel.objects.get(tip=TipDeclaratieTVA.D390, anul=2026, luna=10)
        self.assertEqual(d390.total_de_plata, 0)

    def test_genereaza_luna_goala_redirect(self, _mock):
        response = self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DeclaratieTVAModel.objects.count(), 0)

    def test_marcheaza_platita(self, _mock):
        creeaza_cheltuiala_ue()
        self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 10})
        response = self.client.post(
            reverse("tva-marcheaza-platita"), {"anul": 2026, "luna": 10}
        )
        self.assertEqual(response.status_code, 302)
        d301 = DeclaratieTVAModel.objects.get(tip=TipDeclaratieTVA.D301, anul=2026, luna=10)
        self.assertEqual(d301.status, StatusDeclaratieTVA.PLATITA)

    def test_regenerare_pastreaza_status_platita(self, _mock):
        creeaza_cheltuiala_ue()
        self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 10})
        self.client.post(reverse("tva-marcheaza-platita"), {"anul": 2026, "luna": 10})
        # Regeneram zip-ul: statusul Platita nu trebuie pierdut
        self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 10})
        d301 = DeclaratieTVAModel.objects.get(tip=TipDeclaratieTVA.D301, anul=2026, luna=10)
        self.assertEqual(d301.status, StatusDeclaratieTVA.PLATITA)

    def test_pagina_documente_arata_tabel_tva(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(reverse("documente"), {"anul_tva": 2026})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Declarații TVA")
        self.assertContains(response, "23.57")
        self.assertContains(response, "52937756")

    def test_recipisa_leaga_declaratia(self, _mock):
        creeaza_cheltuiala_ue()
        self.client.get(reverse("tva-genereaza"), {"anul": 2026, "luna": 10})

        # PDF recipisa real din exemplele depuse
        recipisa_path = (
            "stocare/completare-declaratii-tva/DTVA-OCT-2026/"
            "recipisa_d301_cif_52937756_oct_2026_1296415962.pdf"
        )
        with open(recipisa_path, "rb") as f:
            upload = SimpleUploadedFile("recipisa.pdf", f.read(), content_type="application/pdf")

        response = self.client.post(
            reverse("documente"),
            {"tip_document": TipDocument.DOCUMENT_UTIL, "mentiuni": "", "fisier": upload,
             "parse_tip_document": True},
        )
        self.assertEqual(response.status_code, 302)

        doc = DocumenteModel.objects.latest("id")
        self.assertEqual(
            doc.tip_document,
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value,
        )
        d301 = DeclaratieTVAModel.objects.get(tip=TipDeclaratieTVA.D301, anul=2026, luna=10)
        self.assertEqual(d301.status, StatusDeclaratieTVA.DEPUSA)
        self.assertEqual(d301.recipisa_id, doc.id)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_media_"))
@patch("utils.valuta.cursvalutarbnr.get_bnr_rates", side_effect=mock_get_bnr_rates)
class JurnalCumparariRegistreTests(TestCase):

    def setUp(self):
        self.setari = creeaza_setari()

    def test_descarca_jurnal_csv(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("descarca-jurnal-cumparari"),
            {"filetype": "CSV", "anul": 2026, "luna": 10},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("PBW-2026-003576", content)
        self.assertIn("15-16", content)
        self.assertIn("135.81", content)

    def test_descarca_jurnal_pdf(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("descarca-jurnal-cumparari"),
            {"filetype": "PDF", "anul": 2026},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

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
        self.setari = creeaza_setari()

    def test_post_cheltuiala_ue_calculeaza_automat(self, _mock):
        upload = SimpleUploadedFile("factura.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post(reverse("cheltuieli"), {
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
        })
        self.assertEqual(response.status_code, 302)
        c = CheltuialaModel.objects.get(numar_factura="PBW-2026-003576")
        self.assertEqual(c.baza_in_lei, 112.24)
        self.assertEqual(c.tva_autolichidata, 23.57)
        self.assertEqual(c.curs_bnr_aplicat, 5.3447)

    def test_typeahead_furnizor(self, _mock):
        creeaza_cheltuiala_ue()
        response = self.client.get(
            reverse("cheltuieli-cauta-furnizor", args=["cort"])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["furnizor_cod_fiscal"], "ATU77164426")
        self.assertEqual(data[0]["furnizor_tara"], "AT")
