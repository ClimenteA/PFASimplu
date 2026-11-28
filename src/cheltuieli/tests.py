import datetime
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from incasari.models import IncasariModel
from setari.models import SetariModel
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

    def _mijloc_fix(
        self,
        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.value,
        **extra,
    ):
        return CheltuialaModel.objects.create(
            nume_cheltuiala="Echipament",
            suma=D("60000"),
            deductibila=deductibila,
            cod_de_clasificare="2.2.9.",
            ani_amortizare=2,
            data_punerii_in_functiune=datetime.date(2026, 1, 1),
            data_inserarii=datetime.date(2026, 1, 1),
            **extra,
        )

    def test_mijloc_fix_fara_optiune_se_amortizeaza_integral(self):
        mf = self._mijloc_fix()
        self.assertEqual(mf.amortizare_lunara, Decimal("2500"))

    def test_autoturism_m1_limitat_la_1500_lunar(self):
        mf = self._mijloc_fix(Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA_M1.value)
        self.assertEqual(mf.amortizare_lunara, Decimal("1500"))

    def test_autoturism_m1_cu_exceptie(self):
        mf = self._mijloc_fix(
            Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA_M1_EXCEPTIE.value
        )
        self.assertEqual(mf.amortizare_lunara, Decimal("2500"))

    def test_sediu_social_neexclusiv_se_amortizeaza_50_suta(self):
        mf = self._mijloc_fix(
            Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA_SEDIU.value
        )
        self.assertEqual(mf.amortizare_lunara, Decimal("1250"))

    def test_cota_de_amortizare_rotunjita_la_doua_zecimale(self):
        mf = CheltuialaModel.objects.create(
            nume_cheltuiala="Echipament",
            suma=D("36000"),
            deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.value,
            cod_de_clasificare="2.2.9.",
            ani_amortizare=3,
            data_punerii_in_functiune=datetime.date(2026, 1, 1),
            data_inserarii=datetime.date(2026, 1, 1),
        )
        # 36.000 / 36 luni = 1.000 lei/luna -> 2,777...%, afisat 2,78%.
        self.assertEqual(mf.cota_de_amortizare, Decimal("2.78"))


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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_paginare_media_"))
class PaginareTest(TestCase):
    def test_lista_are_20_de_elemente_pe_pagina(self):
        user = User.objects.create_user(username="paginare@test.ro", password="parola")
        self.client.force_login(user)
        for i in range(21):
            CheltuialaModel.objects.create(
                user=user,
                nume_cheltuiala=f"Cheltuiala {i}",
                suma=D("100"),
                data_inserarii=ZIUA,
                fisier=SimpleUploadedFile(f"bon{i}.pdf", b"%PDF-1.4 test"),
            )

        response = self.client.get(reverse("cheltuieli"))
        page_items = response.context["page_items"]
        self.assertEqual(len(list(page_items)), 20)
        self.assertEqual(page_items.paginator.num_pages, 2)

        response = self.client.get(reverse("cheltuieli"), {"page": 2})
        self.assertEqual(len(list(response.context["page_items"])), 1)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_cod_tva_media_"))
class CheltuieliCodTvaTest(TestCase):
    """Filtrul si coloana TVA se afiseaza doar cu cod TVA intracomunitar."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="cheltuieli-cod-tva@test.ro", password="parola"
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

    def test_fara_cod_tva_ascunde_filtrul_si_coloana_tva(self):
        self.setari()

        response = self.client.get(reverse("cheltuieli"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["are_cod_tva"])
        self.assertNotContains(response, 'id="filtru-tva"')
        self.assertNotContains(response, "<th>TVA</th>")

    def test_cu_cod_tva_afiseaza_filtrul_si_coloana_tva(self):
        self.setari("52937756")

        response = self.client.get(reverse("cheltuieli"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["are_cod_tva"])
        self.assertContains(response, 'id="filtru-tva"')
        self.assertContains(response, "<th>TVA</th>")

    def test_fara_cod_tva_filtrul_extern_din_url_e_ignorat(self):
        self.setari()
        CheltuialaModel.objects.create(
            user=self.user,
            nume_cheltuiala="Serviciu extern",
            suma=D("100"),
            data_inserarii=ZIUA,
            data_facturii=ZIUA,
            furnizor_denumire="FURNIZOR GMBH",
            furnizor_cod_fiscal="DE123456789",
            furnizor_tara="DE",
            numar_factura="EXT-1",
            fisier=SimpleUploadedFile("cheltuiala.pdf", b"%PDF-1.4 test"),
        )

        response = self.client.get(reverse("cheltuieli"), {"extern": "1"})

        self.assertFalse(response.context["extern"])
        self.assertEqual(len(response.context["page_items"].object_list), 1)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pfasimplu_test_optiuni_media_"))
class OptiuniMijlocFixInFormTest(TestCase):
    """Optiunile speciale sunt in `Deductibila`, fara checkboxuri separate."""

    def setUp(self):
        user = User.objects.create_user(username="optiuni@test.ro", password="parola")
        self.client.force_login(user)

    def test_formularul_are_variantele_de_mijloc_fix(self):
        response = self.client.get(reverse("cheltuieli"))

        self.assertEqual(response.status_code, 200)
        for eticheta in (
            "Mijloc fix peste 5000 RON (ded. integral cu amortizare)",
            "Mijloc fix peste 5000 RON (sediu social amortizare 50%)",
            "Mijloc fix peste 5000 RON (Autoturism M1 limita 1.500 lei/luna)",
            "Mijloc fix peste 5000 RON (Autoturism M1 cu exceptie art. 28 alin. 14, amortizare integrala)",
        ):
            self.assertContains(response, eticheta)
        for camp in (
            "este_sediu_social_neexclusiv",
            "este_autoturism_m1",
            "exceptie_1500",
        ):
            self.assertNotContains(response, f"id_{camp}")
