import datetime
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from facturi.models import FacturaModel
from setari.models import SetariModel
from utils.decimale import D
from utils.valuta import TipTranzactie
from utils.views import get_cautare

from .models import IncasariModel, SursaVenit
from .views import CAUTARE_COLOANE


class IncasariAlteSurseTest(TestCase):
    def test_totalul_exclude_activitatea_principala(self):
        IncasariModel.objects.create(
            suma=D("100"),
            sursa_venit=SursaVenit.ACTIVITATE_PRINCIPALA.value,
            data_incasarii=datetime.date(2026, 1, 10),
        )
        IncasariModel.objects.create(
            suma=D("50"),
            sursa_venit=SursaVenit.DIVIDENTE_VENIT_DISTRUBUIT.value,
            data_incasarii=datetime.date(2026, 1, 11),
        )
        self.assertEqual(
            IncasariModel.get_total_incasari_alte_surse(2026), Decimal("50")
        )


class IncasareDinFacturaTest(TestCase):
    """Precompletarea formularului de incasare pornit din pagina Facturi."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="incasare-factura@test.ro", password="parola"
        )
        self.client.force_login(self.user)

    def creeaza_factura(self, numar, tip_tranzactie):
        return FacturaModel.objects.create(
            user=self.user,
            serie="INV",
            numar=numar,
            nume="Client test",
            cif="RO1234567",
            adresa="Strada Test nr. 1",
            tip_tranzactie=tip_tranzactie,
        )

    def test_tip_tranzactie_bancar_se_pastreaza_din_factura(self):
        factura = self.creeaza_factura(1, TipTranzactie.BANCAR.value)

        response = self.client.get("/incasari/", {"factura_id": factura.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["incasari_form"].initial["tip_tranzactie"],
            TipTranzactie.BANCAR.value,
        )

    def test_tip_tranzactie_numerar_se_pastreaza_din_factura(self):
        factura = self.creeaza_factura(2, TipTranzactie.NUMERAR.value)

        response = self.client.get("/incasari/", {"factura_id": factura.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["incasari_form"].initial["tip_tranzactie"],
            TipTranzactie.NUMERAR.value,
        )

    def test_nume_incasare_se_precompleteaza_cu_clientul_si_factura(self):
        factura = self.creeaza_factura(3, TipTranzactie.BANCAR.value)

        response = self.client.get("/incasari/", {"factura_id": factura.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["incasari_form"].initial["nume_incasare"],
            "CLIENT TEST - INV-3",
        )
        self.assertEqual(factura.nume, "CLIENT TEST")

    def test_cautare_dupa_nume_incasare(self):
        IncasariModel.objects.create(suma=D("100"), nume_incasare="Client Alfa")
        IncasariModel.objects.create(suma=D("100"), nume_incasare="Client Beta")

        request = RequestFactory().get(
            "/incasari/", {"coloana": "nume_incasare", "cauta": "alfa"}
        )
        query, context = get_cautare(request, CAUTARE_COLOANE)

        self.assertIn(("nume_incasare", "Nume incasare"), context["coloane_cautare"])
        rezultate = list(IncasariModel.objects.filter(query))
        self.assertEqual(len(rezultate), 1)
        self.assertEqual(rezultate[0].nume_incasare, "Client Alfa")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_cod_tva_media_"))
class IncasariCodTvaTest(TestCase):
    """Filtrul si coloana VIES se afiseaza doar cu cod TVA intracomunitar."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="incasari-cod-tva@test.ro", password="parola"
        )
        self.client.force_login(self.user)

    def setari(self, cod_tva=""):
        return SetariModel.objects.create(
            user=self.user,
            nume="TEST PFA",
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa="Strada Test nr. 1",
            nr_reg_com="F1",
            cif="1234567",
            email="test@test.ro",
            caen_principal="6201",
            cod_tva_intracomunitar=cod_tva,
        )

    def test_fara_cod_tva_ascunde_filtrul_si_coloana_vies(self):
        self.setari()

        response = self.client.get("/incasari/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["are_cod_tva"])
        self.assertNotIn(("ue", "VIES"), response.context["coloane_cautare"])
        self.assertNotContains(response, 'id="filtru-incasari-ue"')
        self.assertNotContains(response, "<th>VIES</th>")

    def test_cu_cod_tva_afiseaza_filtrul_si_coloana_vies(self):
        self.setari("52937756")

        response = self.client.get("/incasari/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["are_cod_tva"])
        self.assertIn(("ue", "VIES"), response.context["coloane_cautare"])
        self.assertContains(response, 'id="filtru-incasari-ue"')
        self.assertContains(response, "<th>VIES</th>")

    def test_fara_cod_tva_filtrul_ue_din_url_e_ignorat(self):
        self.setari()
        factura = FacturaModel.objects.create(
            user=self.user,
            serie="INV",
            numar=1,
            nume="Client UE",
            cif="DE123",
            adresa="Strada Test nr. 1",
            client_ue=True,
        )
        IncasariModel.objects.create(
            user=self.user,
            factura=factura,
            suma=D("100"),
            nume_incasare="Client UE",
            fisier=SimpleUploadedFile("incasare.pdf", b"%PDF-1.4 test"),
        )

        response = self.client.get("/incasari/", {"ue": "1"})

        self.assertFalse(response.context["ue"])
        self.assertEqual(len(response.context["page_items"].object_list), 1)
