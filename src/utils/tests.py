import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from documente.models import DocumenteModel, TipDocument
from facturi.models import FacturaModel
from utils.calcule import calculeaza_cass_trepte, calculeaza_taxe_si_impozite
from utils.decimale import D, rotund2, suma
from utils.parametri import get_parametri
from utils.views import download_model_csv_or_xlsx, get_cautare
from utils.widgets import NumeFisierFileInput


class RotunjiriTest(SimpleTestCase):
    def test_calculul_intermediar_pastreaza_toate_zecimalele(self):
        # 112.2387 x 0.21 = 23.570127, fara rotunjire la 4 zecimale.
        self.assertEqual(D("112.2387") * D("0.21"), Decimal("23.570127"))

    def test_suma_finala_la_doua_zecimale(self):
        self.assertEqual(rotund2(Decimal("23.570127")), Decimal("23.57"))
        self.assertEqual(rotund2(Decimal("23.575")), Decimal("23.58"))
        self.assertEqual(
            suma([Decimal("112.2387"), Decimal("23.570127")]),
            Decimal("135.808827"),
        )


class ParametriFiscaliTest(SimpleTestCase):
    def test_valori_si_fallback_pe_ani(self):
        self.assertEqual(get_parametri(2026)["salariu_minim_brut"], 4050)
        self.assertEqual(get_parametri(2027)["salariu_minim_brut"], 4325)
        # parametrii neschimbati se mostenesc de la 2026
        self.assertEqual(get_parametri(2027)["cote"]["cas"], 0.25)
        self.assertEqual(get_parametri(2027)["cass_salarii"]["max"], 72)
        # pentru anii anteriori primei configuratii se foloseste 2026
        self.assertEqual(get_parametri(2025)["salariu_minim_brut"], 4050)


class CassTrepteTest(SimpleTestCase):
    def test_sub_prima_treapta(self):
        self.assertEqual(calculeaza_cass_trepte(Decimal("10000"), 2026), Decimal("0"))

    def test_treapta_6_salarii(self):
        self.assertEqual(
            calculeaza_cass_trepte(Decimal("30000"), 2026), Decimal("2430.0000")
        )

    def test_treapta_12_salarii(self):
        self.assertEqual(
            calculeaza_cass_trepte(Decimal("50000"), 2026), Decimal("4860.0000")
        )

    def test_treapta_24_salarii_cu_plafon(self):
        self.assertEqual(
            calculeaza_cass_trepte(Decimal("300000"), 2026), Decimal("9720.0000")
        )

    def test_combinare_cu_activitatea_independenta(self):
        rezultat = calculeaza_taxe_si_impozite(
            Decimal("30000"), 2026, alte_venituri=Decimal("30000")
        )
        self.assertEqual(rezultat["cass_sanatate"], Decimal("2430.00"))


class CalculeazaTaxeTest(SimpleTestCase):
    def test_exemplu_30000_lei(self):
        rezultat = calculeaza_taxe_si_impozite(Decimal("30000"), 2026)
        self.assertEqual(rezultat["cas_pensie"], Decimal("0.00"))
        self.assertEqual(rezultat["cass_sanatate"], Decimal("3000.00"))
        self.assertEqual(rezultat["impozit_pe_venit"], Decimal("2700.00"))
        self.assertEqual(rezultat["total_taxe_impozite"], Decimal("5700.00"))

    def test_exemplu_50000_lei(self):
        rezultat = calculeaza_taxe_si_impozite(Decimal("50000"), 2026)
        self.assertEqual(rezultat["cas_pensie"], Decimal("12150.00"))
        self.assertEqual(rezultat["cass_sanatate"], Decimal("5000.00"))
        self.assertEqual(rezultat["impozit_pe_venit"], Decimal("3285.00"))
        self.assertEqual(rezultat["total_taxe_impozite"], Decimal("20435.00"))

    def test_exemplu_300000_lei_cu_plafon_cass(self):
        rezultat = calculeaza_taxe_si_impozite(Decimal("300000"), 2026)
        self.assertEqual(rezultat["cas_pensie"], Decimal("24300.00"))
        self.assertEqual(rezultat["cass_sanatate"], Decimal("29160.00"))
        self.assertEqual(rezultat["impozit_pe_venit"], Decimal("24654.00"))
        self.assertEqual(rezultat["total_taxe_impozite"], Decimal("78114.00"))

    def test_scutiri(self):
        rezultat = calculeaza_taxe_si_impozite(
            Decimal("100000"), 2026, True, True, True
        )
        self.assertEqual(rezultat["total_taxe_impozite"], Decimal("0.00"))


class CautareTabelTest(TestCase):
    COLOANE = {
        "tip_document": ("Tip document", ["tip_document"]),
        "mentiuni": ("Mentiuni", ["mentiuni"]),
    }

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username="cautare@test.ro", password="parola"
        )
        DocumenteModel.objects.create(
            user=self.user,
            tip_document=TipDocument.DOCUMENT_UTIL,
            mentiuni="Platit factura de electricitate",
            fisier="documente/1.pdf",
        )
        DocumenteModel.objects.create(
            user=self.user,
            tip_document=TipDocument.DECLARATIE_UNICA_212,
            mentiuni="Dovada depunerii",
            fisier="documente/2.pdf",
        )
        DocumenteModel.objects.create(
            user=self.user,
            tip_document=TipDocument.DOCUMENT_UTIL,
            mentiuni="D212 depusa la ghiseu",
            fisier="documente/3.pdf",
        )

    def test_fara_coloana_cauta_in_toate_coloanele(self):
        request = self.factory.get("/documente/", {"cauta": "D212"})
        query, context = get_cautare(request, self.COLOANE)

        rezultate = list(DocumenteModel.objects.filter(query))
        self.assertEqual(len(rezultate), 2)
        self.assertEqual(
            {d.tip_document for d in rezultate},
            {TipDocument.DECLARATIE_UNICA_212, TipDocument.DOCUMENT_UTIL},
        )
        self.assertEqual(context["coloana"], "")
        self.assertEqual(
            context["coloane_cautare"][0], ("tip_document", "Tip document")
        )

    def test_cu_coloana_cauta_doar_in_coloana_selectata(self):
        request = self.factory.get(
            "/documente/", {"cauta": "D212", "coloana": "mentiuni"}
        )
        query, context = get_cautare(request, self.COLOANE)
        self.assertEqual(
            [d.mentiuni for d in DocumenteModel.objects.filter(query)],
            ["D212 depusa la ghiseu"],
        )

        request = self.factory.get(
            "/documente/", {"cauta": "D212", "coloana": "tip_document"}
        )
        query, context = get_cautare(request, self.COLOANE)
        self.assertEqual(
            [d.mentiuni for d in DocumenteModel.objects.filter(query)],
            ["Dovada depunerii"],
        )
        self.assertEqual(context["coloana"], "tip_document")

    def test_coloana_necunoscuta_revine_la_toate_coloanele(self):
        request = self.factory.get("/documente/", {"cauta": "D212", "coloana": "x"})
        query, context = get_cautare(request, self.COLOANE)
        self.assertEqual(DocumenteModel.objects.filter(query).count(), 2)
        self.assertEqual(context["coloana"], "")

    def test_pastrare_parametri_fara_delete_id(self):
        request = self.factory.get(
            "/cheltuieli/",
            {
                "cauta": "Cort",
                "coloana": "nume_cheltuiala",
                "extern": "1",
                "anul_extern": "2026",
                "page": "2",
                "delete_id": "7",
            },
        )
        query, context = get_cautare(
            request, {"nume_cheltuiala": ("Nume", ["nume_cheltuiala"])}
        )
        self.assertEqual(
            dict(context["parametri_pastrati"]),
            {"extern": "1", "anul_extern": "2026"},
        )
        self.assertIn("cauta=Cort", context["query_cautare"])
        self.assertIn("coloana=nume_cheltuiala", context["query_cautare"])
        self.assertNotIn("delete_id", context["query_cautare"])

    def test_cautare_in_camp_numeric_si_data(self):
        FacturaModel.objects.create(
            user=self.user,
            serie="INV",
            numar=1234,
            nume="Client test",
            cif="RO123",
            adresa="Strada Testului",
            data_scadenta=datetime.date(2026, 11, 27),
        )
        for camp, termen in (("numar", "1234"), ("data_scadenta", "2026-11")):
            with self.subTest(camp=camp):
                request = self.factory.get(
                    "/facturi/", {"cauta": termen, "coloana": camp}
                )
                query, _ = get_cautare(request, {camp: (camp, [camp])})
                self.assertEqual(FacturaModel.objects.filter(query).count(), 1)

    def test_pagina_documente_are_filtru_si_filtreaza(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("documente"), {"cauta": "electricitate"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="cauta"')
        self.assertContains(response, 'name="coloana"')
        self.assertContains(response, "Toate coloanele")
        self.assertEqual(
            [d.pk for d in response.context["page_items"]],
            [DocumenteModel.objects.get(mentiuni="Platit factura de electricitate").pk],
        )


class NumeFisierWidgetTest(SimpleTestCase):
    def test_widgetul_afiseaza_doar_numele_fisierului(self):
        nume = "XgERGebX_doc_cheltuiala_2026_02_05.pdf"

        class Fisier:
            name = f"user_1/{nume}"
            url = f"/media/user_1/{nume}"

        html = NumeFisierFileInput().render("fisier", Fisier(), {"id": "id_fisier"})

        self.assertIn(f">{nume}</a>", html)
        self.assertIn(f'href="{Fisier.url}"', html)
        self.assertNotIn(f"user_1/{nume}</a>", html)


class ExportNumeFisierTest(TestCase):
    @patch("utils.views.download_dataframe")
    def test_exportul_nu_contine_prefixul_de_folder(self, download_dataframe):
        nume = "XgERGebX_doc_cheltuiala_2026_02_05.pdf"
        DocumenteModel.objects.create(fisier=f"user_1/{nume}")

        request = RequestFactory().get("/documente/", {"filetype": "csv"})
        download_model_csv_or_xlsx(
            request, DocumenteModel, "documente", order_by="-actualizat_la"
        )

        df = download_dataframe.call_args.args[1]
        self.assertEqual(df.loc[0, "fisier"], nume)
