from decimal import Decimal

from django.test import SimpleTestCase

from utils.calcule import calculeaza_cass_trepte, calculeaza_taxe_si_impozite
from utils.decimale import D, rotund2, suma
from utils.parametri import get_parametri


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
