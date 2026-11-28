"""Teste pentru emitenta de pe factura (CIF vs. cod TVA intracomunitar)."""

import json

from django.contrib.auth.models import User
from django.test import TestCase

from facturi.forms import FacturaForm
from facturi.generare import construieste_context
from facturi.models import (
    NOTA_TAXARE_INVERSA_VIES,
    FacturaModel,
    nota_taxare_inversa_vies,
)
from setari.models import SetariModel


class CifFurnizorFacturaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@pfasimplu.ro")
        self.setari = SetariModel.objects.create(
            user=self.user,
            nume="PFA TEST",
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa="Strada Testului 1",
            nr_reg_com="F22/123/2020",
            cif="RO12345678",
            email="test@example.com",
            caen_principal="6201",
            cod_tva_intracomunitar="52937756",
        )
        self.factura = FacturaModel.objects.create(
            user=self.user,
            serie="INV",
            numar=1,
            nume="CLIENT TEST",
            cif="ATU12345678",
            adresa="Strada Clientului 2",
        )

    def test_switch_client_ue_default_false(self):
        self.assertFalse(FacturaModel().client_ue)
        self.assertEqual(
            FacturaForm().fields["client_ue"].widget.attrs["role"], "switch"
        )

    def test_client_ue_foloseste_codul_tva_cu_prefix_ro(self):
        self.factura.client_ue = True
        context = construieste_context(self.factura)
        self.assertEqual(context["cif_furnizor"], "RO52937756")

    def test_client_non_ue_foloseste_cif_normal(self):
        context = construieste_context(self.factura)
        self.assertEqual(context["cif_furnizor"], "RO12345678")

    def test_cod_tva_cu_prefix_in_setari_nu_se_dubleaza(self):
        self.setari.cod_tva_intracomunitar = "RO52937756"
        self.setari.save(update_fields=["cod_tva_intracomunitar"])
        self.factura.client_ue = True
        context = construieste_context(self.factura)
        self.assertEqual(context["cif_furnizor"], "RO52937756")

    def test_client_ue_fara_cod_tva_cade_inapoi_pe_cif(self):
        self.setari.cod_tva_intracomunitar = None
        self.setari.save(update_fields=["cod_tva_intracomunitar"])
        self.factura.client_ue = True
        context = construieste_context(self.factura)
        self.assertEqual(context["cif_furnizor"], "RO12345678")

    def test_eticheta_client_ue_vies(self):
        self.assertTrue(
            FacturaForm().fields["client_ue"].label.lower().endswith("vies")
        )


class NotaClientUEVIESTest(TestCase):
    def form_data(self, numar, tip_factura="factura-engleza", client_ue=True, nota=""):
        return {
            "serie": "INV",
            "numar": numar,
            "nume": "CLIENT UE",
            "cif": "ATU12345678",
            "adresa": "STRADA TESTULUI 1",
            "data_emitere": "2026-10-02",
            "data_scadenta": "2026-11-02",
            "tip_factura": tip_factura,
            "tip_tranzactie": "BANCAR",
            "valuta": "EUR",
            "client_ue": "on" if client_ue else "",
            "nota": nota,
            "produse_sau_servicii": json.dumps(
                [
                    {
                        "nume_produs_sau_serviciu": "Consultanta",
                        "cod_unitate": "HUR",
                        "numar_unitati": 1,
                        "pret_pe_unitate": 100,
                    }
                ]
            ),
        }

    def test_nota_auto_in_limba_facturii(self):
        for numar, (tip, asteptat) in enumerate(
            NOTA_TAXARE_INVERSA_VIES.items(), start=100
        ):
            form = FacturaForm(self.form_data(numar, tip_factura=tip))
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().nota, asteptat)

    def test_nota_scrisa_manual_nu_se_suprascrie(self):
        form = FacturaForm(self.form_data(200, nota="Mentiunea mea"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().nota, "Mentiunea mea")

    def test_fara_client_ue_nota_ramane_goala(self):
        form = FacturaForm(self.form_data(201, client_ue=False))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().nota, "")

    def test_debifarea_sterge_nota_auto(self):
        form = FacturaForm(
            self.form_data(
                202,
                client_ue=False,
                nota=NOTA_TAXARE_INVERSA_VIES["factura-engleza"],
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().nota, "")

    def test_limba_necunoscuta_revine_la_romana(self):
        self.assertEqual(
            nota_taxare_inversa_vies("necunoscut"),
            NOTA_TAXARE_INVERSA_VIES["e-factura"],
        )

    def test_client_ue_cu_cif_romanesc_este_respins(self):
        date = self.form_data(203)
        date["cif"] = "RO12345678"
        form = FacturaForm(date)
        self.assertFalse(form.is_valid())
        self.assertIn("cif", form.errors)
        self.assertIn("prefixul tarii UE", str(form.errors["cif"]))

    def test_client_ue_cu_cif_fara_prefix_este_respins(self):
        date = self.form_data(204)
        date["cif"] = "12345678"
        form = FacturaForm(date)
        self.assertFalse(form.is_valid())
        self.assertIn("cif", form.errors)

    def test_client_ue_cu_prefix_non_ue_este_respins(self):
        date = self.form_data(205)
        date["cif"] = "US12345678"
        form = FacturaForm(date)
        self.assertFalse(form.is_valid())
        self.assertIn("cif", form.errors)

    def test_client_non_ue_cu_cif_romanesc_se_salveaza(self):
        date = self.form_data(206, client_ue=False)
        date["cif"] = "RO12345678"
        form = FacturaForm(date)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().cif, "RO12345678")


class FacturaEroareValidareTest(TestCase):
    """Dupa o eroare de validare, formularul isi pastreaza valorile completate."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="rerandare@test.ro", password="parola"
        )
        self.client.force_login(self.user)
        SetariModel.objects.create(
            user=self.user,
            nume="TEST PFA",
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa="Strada Test nr. 1",
            nr_reg_com="F1",
            cif="1234567",
            email="test@test.ro",
            caen_principal="6201",
            cod_tva_intracomunitar="52937756",
        )

    def test_eroarea_pastreaza_campurile_si_liniile(self):
        linii = json.dumps(
            [
                {
                    "id": 1,
                    "nume_produs_sau_serviciu": "Consultanta",
                    "cod_unitate": "HUR",
                    "numar_unitati": "1.00",
                    "pret_pe_unitate": "100.00",
                    "subtotal": "100.00",
                }
            ]
        )
        response = self.client.post(
            "/facturi/",
            {
                "serie": "VAL",
                "numar": 7,
                "nume": "CLIENT DE TEST",
                "cif": "12345678",  # fara prefix UE -> eroare de validare
                "adresa": "STRADA TESTULUI 1",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "data_emitere": "2026-10-02",
                "data_scadenta": "2026-11-01",
                "tip_factura": "factura-germana",
                "tip_tranzactie": "BANCAR",
                "valuta": "USD",
                "client_ue": "on",
                "nota": "",
                "produse_sau_servicii": linii,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("cif", response.context["facturi_form"].errors)
        html = response.content.decode()
        for valoare in (
            "CLIENT DE TEST",
            "12345678",
            "VAL",
            "2026-10-02",
            "2026-11-01",
            "RO-IS, jud. Iasi, Iasi",
            "Consultanta",
        ):
            self.assertIn(valoare, html)
        # Alpine isi initializeaza starea din valorile randate de Django.
        self.assertIn("numeClient: 'CLIENT DE TEST'", html)
        self.assertIn("moreFields: true", html)


class FacturiCodTvaTest(TestCase):
    """Switchul si helperul Client UE VIES apar doar cu cod TVA intracomunitar."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="facturi-cod-tva@test.ro", password="parola"
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

    def test_fara_cod_tva_ascunde_switchul_si_helperul(self):
        self.setari()

        response = self.client.get("/facturi/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["are_cod_tva"])
        self.assertNotContains(response, 'id="id_client_ue"')
        self.assertNotContains(response, "Client UE VIES")
        self.assertNotContains(response, 'id="cif-helper"')
        self.assertNotContains(response, "Pentru client UE VIES")

    def test_cu_cod_tva_afiseaza_switchul_si_helperul(self):
        self.setari("52937756")

        response = self.client.get("/facturi/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["are_cod_tva"])
        self.assertContains(response, 'id="id_client_ue"')
        self.assertContains(response, "Client UE VIES")
        self.assertContains(response, 'id="cif-helper"')
        self.assertContains(response, "Pentru client UE VIES")
