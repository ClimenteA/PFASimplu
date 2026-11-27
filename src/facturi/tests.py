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
