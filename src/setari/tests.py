"""Teste pentru detectia versiunii noi afisate in pagina Setari."""

from django.test import SimpleTestCase

from setari.views import _este_versiune_mai_noua


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
