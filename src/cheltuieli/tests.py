import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from incasari.models import IncasariModel
from utils.cursuri import to_ron
from utils.decimale import D

from .calcul import _CACHE, calculeaza_deduceri_anului
from .models import CheltuialaModel, Deductibilitate

ZIUA = datetime.date(2026, 2, 1)


class DeduceriNoiTest(TestCase):
    def setUp(self):
        _CACHE.clear()

    def _incasare(self, suma):
        IncasariModel.objects.create(
            suma=D(suma),
            data_incasarii=datetime.date(2026, 1, 10),
            data_inserarii=datetime.date(2026, 1, 10),
        )

    def _cheltuiala(self, cod, suma, **extra):
        return CheltuialaModel.objects.create(
            nume_cheltuiala="Cheltuiala test",
            suma=D(suma),
            deductibila=cod,
            data_inserarii=ZIUA,
            **extra,
        )

    def test_burse_private_limitate_la_5_suta_din_baza(self):
        self._incasare("100000")
        self._cheltuiala(Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE.value, "3000")
        self.assertEqual(
            calculeaza_deduceri_anului(2026)[
                CheltuialaModel.objects.get(
                    deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE.value
                ).pk
            ],
            Decimal("3000"),
        )

        candidat = CheltuialaModel(
            nume_cheltuiala="Bursa in plus",
            suma=D("6000"),
            deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE.value,
            data_inserarii=ZIUA,
        )
        with self.assertRaises(ValidationError):
            calculeaza_deduceri_anului(2026, candidat=candidat)

    def test_protocol_ignora_ordinea_inserarii(self):
        self._incasare("100000")
        self._cheltuiala(Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE.value, "3000")
        self._cheltuiala(Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value, "1940")
        # 2% din (100.000 - 3.000 burse) = 1.940 lei
        self.assertEqual(
            sum(calculeaza_deduceri_anului(2026).values()), Decimal("4940")
        )

    def test_plafon_eur_pensie_ocupationala(self):
        cap = to_ron(400, "EUR", ZIUA)
        self._cheltuiala(
            Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_OCUPATIONALA.value, cap
        )
        candidat = CheltuialaModel(
            nume_cheltuiala="Pensie ocupationala in plus",
            suma=D(cap) + D("1"),
            deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_OCUPATIONALA.value,
            data_inserarii=ZIUA,
        )
        with self.assertRaises(ValidationError):
            calculeaza_deduceri_anului(2026, candidat=candidat)


class AmortizareLimitataTest(TestCase):
    def setUp(self):
        _CACHE.clear()

    def _mijloc_fix(self, **extra):
        return CheltuialaModel.objects.create(
            nume_cheltuiala="Echipament",
            suma=D("60000"),
            deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.value,
            cod_de_clasificare="2.2.9.",
            ani_amortizare=2,
            data_punerii_in_functiune=datetime.date(2026, 1, 1),
            data_inserarii=datetime.date(2026, 1, 1),
            **extra,
        )

    def test_autoturism_m1_limitat_la_1500_lunar(self):
        mf = self._mijloc_fix(este_autoturism_m1=True)
        self.assertEqual(mf.amortizare_lunara, Decimal("1500"))

    def test_autoturism_m1_cu_exceptie(self):
        mf = self._mijloc_fix(este_autoturism_m1=True, exceptie_1500=True)
        self.assertEqual(mf.amortizare_lunara, Decimal("2500"))

    def test_sediu_social_neexclusiv_se_amortizeaza_50_suta(self):
        mf = self._mijloc_fix(este_sediu_social_neexclusiv=True)
        self.assertEqual(mf.amortizare_lunara, Decimal("1250"))


class CotaTvaTest(TestCase):
    def _cheltuiala_externa(self):
        return CheltuialaModel.objects.create(
            nume_cheltuiala="Serviciu extern",
            suma=D("100"),
            data_inserarii=datetime.date(2026, 1, 15),
            data_facturii=datetime.date(2026, 1, 15),
            furnizor_denumire="FURNIZOR GMBH",
            furnizor_cod_fiscal="DE123456789",
            furnizor_tara="DE",
            numar_factura="EXT-1",
        )

    def test_tva_autolichidata_la_cota_standard(self):
        self.assertEqual(
            self._cheltuiala_externa().tva_autolichidata, Decimal("21.0000")
        )

    def test_furnizor_roman_nu_are_tva_autolichidata(self):
        cheltuiala = CheltuialaModel.objects.create(
            nume_cheltuiala="Serviciu local",
            suma=D("100"),
            data_inserarii=datetime.date(2026, 1, 15),
        )
        self.assertIsNone(cheltuiala.tva_autolichidata)
