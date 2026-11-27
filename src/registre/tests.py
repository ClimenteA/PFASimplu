import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from facturi.models import FacturaModel, LinieFactura
from setari.models import SetariModel
from utils.decimale import D


class JurnalVanzariRegistreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="registre@test.ro")
        self.client.force_login(self.user)
        SetariModel.objects.create(
            user=self.user,
            nume="PFA TEST",
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa="Strada Testului 1",
            nr_reg_com="F22/123/2020",
            cif="43000098",
            email="test@example.com",
            caen_principal="6201",
        )

    def creeaza_factura(self, numar, client_ue):
        factura = FacturaModel.objects.create(
            user=self.user,
            serie="INV",
            numar=numar,
            nume="CLIENT UE" if client_ue else "CLIENT RO",
            cif="ATU77164426" if client_ue else "RO1234567",
            adresa="Strada Client nr. 1",
            client_ue=client_ue,
            data_emitere=datetime.date(2026, 10, 2),
            valuta="RON",
        )
        LinieFactura.objects.create(
            factura=factura,
            nume="Servicii",
            cantitate=1,
            pret_unitar=100 if client_ue else 50,
        )
        return factura

    def test_jurnal_vanzari_doar_clienti_ue_vies(self):
        self.creeaza_factura(1, True)
        self.creeaza_factura(2, False)

        response = self.client.get("/registre/?anul=2026")

        self.assertEqual(response.status_code, 200)
        jurnal = response.context["rjv"]
        self.assertEqual(len(jurnal["randuri"]), 1)
        rand = jurnal["randuri"][0]
        self.assertEqual(rand["nr_doc"], "INV-1")
        self.assertEqual(rand["client_cod_fiscal"], "U77164426")
        self.assertEqual(rand["baza"], D("100.0000"))
        self.assertContains(response, "Jurnal Vanzari")

    def test_download_csv_si_xlsx(self):
        self.creeaza_factura(1, True)

        for filetype, extensie in (("CSV", "csv"), ("XLSX", "xlsx")):
            response = self.client.get(
                reverse("descarca-jurnal-vanzari"),
                {"filetype": filetype, "anul": 2026, "valuta": "RON"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                f"jurnal_vanzari_2026.{extensie}", response["Content-Disposition"]
            )
            self.assertGreater(len(response.content), 0)

    def test_luna_fara_facturi_ue_redirect(self):
        self.creeaza_factura(1, True)
        response = self.client.get(
            reverse("descarca-jurnal-vanzari"),
            {"filetype": "CSV", "anul": 2026, "luna": 11},
        )
        self.assertRedirects(response, "/registre/")
