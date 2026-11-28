"""Teste pentru pagina Setari: versiunea noua si exportul datelor."""

import csv
import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from cheltuieli.calcul import _CACHE
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from setari.forms import SetariForm
from setari.models import SetariModel
from setari.views import _este_versiune_mai_noua, salveaza_tabele_csv
from utils.decimale import D


class VersiuneNouaTests(SimpleTestCase):
    def test_versiunea_noua_e_detectata(self):
        self.assertTrue(_este_versiune_mai_noua("3.1.0", "3.0.4"))
        self.assertTrue(_este_versiune_mai_noua("10.0.0", "9.9.9"))

    def test_versiunea_egala_sau_mai_veche_nu_e_detectata(self):
        self.assertFalse(_este_versiune_mai_noua("3.0.4", "3.0.4"))
        self.assertFalse(_este_versiune_mai_noua("3.0.3", "3.0.4"))

    def test_versiunea_invalidata(self):
        for remote, local in (("", "3.0.4"), ("3.0", "3.0.4"), ("3.0.4", "")):
            with self.subTest(remote=remote, local=local):
                self.assertFalse(_este_versiune_mai_noua(remote, local))


class EmailDinLogareTest(TestCase):
    """Campul email e precompletat cu emailul de logare doar cat timp e gol."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="login@test.ro", email="login@test.ro", password="parola"
        )
        self.client.force_login(self.user)

    def _email_din_formular(self):
        response = self.client.get("/setari/")
        self.assertEqual(response.status_code, 200)
        return response.context["setari_form"].initial["email"]

    def _creeaza_setari(self, email):
        return SetariModel.objects.create(
            user=self.user,
            nume="PFA Test",
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa="Strada Testului 1",
            nr_reg_com="F22/1/2020",
            cif="RO12345678",
            email=email,
            caen_principal="6201",
        )

    def test_fara_setari_se_precompleteaza_cu_emailul_de_logare(self):
        self.assertEqual(self._email_din_formular(), "login@test.ro")

    def test_email_gol_se_precompleteaza_cu_emailul_de_logare(self):
        self._creeaza_setari(email="")
        self.assertEqual(self._email_din_formular(), "login@test.ro")

    def test_email_actualizat_de_utilizator_nu_mai_e_precompletat(self):
        self._creeaza_setari(email="contact@pfa.ro")
        self.assertEqual(self._email_din_formular(), "contact@pfa.ro")


class CaenSecundareTest(TestCase):
    """Totalul e de 5 coduri CAEN: 1 principal + 4 secundare."""

    def test_formularul_are_patru_campuri_secundare(self):
        campuri = [n for n in SetariForm().fields if n.startswith("caen_secondar_")]
        self.assertEqual(campuri, [f"caen_secondar_{i}" for i in range(1, 5)])

    def test_se_salveaza_cel_mult_patru_coduri_secundare(self):
        form = SetariForm(
            data={
                "nume": "PFA Test",
                "localitate": "RO-IS, jud. Iasi, Iasi",
                "adresa": "Strada Testului 1",
                "nr_reg_com": "F22/1/2020",
                "cif": "RO12345678",
                "email": "contact@pfa.ro",
                "caen_principal": "6201",
                "caen_secondar_1": "1111",
                "caen_secondar_2": "2222",
                "caen_secondar_3": "3333",
                "caen_secondar_4": "4444",
                "conturi_iban": "[]",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().caen_secondare, ["1111", "2222", "3333", "4444"])


class ExportTabeleCsvTest(TestCase):
    def setUp(self):
        _CACHE.clear()

    def test_exporta_incasari_si_cheltuieli_cu_sume_exacte(self):
        IncasariModel.objects.create(
            nume_incasare="Client Alfa",
            suma=D("1234.56"),
            data_inserarii=datetime.date(2026, 2, 10),
            data_incasarii=datetime.date(2026, 2, 10),
            fisier="user_1/bon_incasare.pdf",
        )
        CheltuialaModel.objects.create(
            nume_cheltuiala="Energie",
            suma=D("99.87"),
            data_inserarii=datetime.date(2026, 2, 11),
            fisier="user_1/factura_energie.pdf",
        )

        with tempfile.TemporaryDirectory() as folder:
            fisiere = salveaza_tabele_csv(folder)
            self.assertEqual(
                [os.path.basename(fp) for fp in fisiere],
                ["incasari.csv", "cheltuieli.csv"],
            )

            with open(fisiere[0], encoding="utf-8", newline="") as f:
                incasari = list(csv.DictReader(f))
            self.assertEqual(len(incasari), 1)
            self.assertEqual(incasari[0]["nume_incasare"], "Client Alfa")
            self.assertEqual(incasari[0]["suma"], "1234.56")
            self.assertEqual(incasari[0]["fisier"], "bon_incasare.pdf")

            with open(fisiere[1], encoding="utf-8", newline="") as f:
                cheltuieli = list(csv.DictReader(f))
            self.assertEqual(len(cheltuieli), 1)
            self.assertEqual(cheltuieli[0]["nume_cheltuiala"], "Energie")
            self.assertEqual(cheltuieli[0]["suma"], "99.87")
            self.assertEqual(cheltuieli[0]["fisier"], "factura_energie.pdf")
