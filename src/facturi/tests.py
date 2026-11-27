"""Teste pentru emitenta de pe factura (CIF vs. cod TVA intracomunitar)."""

from django.contrib.auth.models import User
from django.test import TestCase

from facturi.forms import FacturaForm
from facturi.generare import construieste_context
from facturi.models import FacturaModel
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
