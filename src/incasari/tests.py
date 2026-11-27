import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from facturi.models import FacturaModel
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
