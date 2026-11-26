"""Teste pentru actualizarea executabilului standalone din pagina Setari."""

import io
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from utils.actualizare import (
    EroareActualizare,
    calea_executabilului,
    descarca_executabil,
    este_standalone,
    nume_asset,
    url_actualizare,
)


class RaspunsFals:
    """Minim context-manager pentru requests.get(stream=True)."""

    def __init__(self, continut: bytes):
        self.continut = continut

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        yield self.continut


def arhiva_cu(nume: str, continut: bytes = b"EXE-FALS") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as arhiva:
        arhiva.writestr(nume, continut)
    return buf.getvalue()


class NumeAssetTests(TestCase):
    @patch("utils.actualizare._platforma", return_value=("linux", "x86_64"))
    def test_nume_si_url_linux(self, _platforma):
        self.assertEqual(nume_asset("3.0.1"), "pfasimplu-3.0.1-linux-x86_64")
        self.assertEqual(
            url_actualizare("3.0.1"),
            "https://github.com/ClimenteA/PFASimplu/releases/download/"
            "v3.0.1/pfasimplu-3.0.1-linux-x86_64.zip",
        )

    @patch("utils.actualizare._platforma", return_value=("windows", "x86_64"))
    def test_nume_windows_are_exec(self, _platforma):
        self.assertEqual(nume_asset("3.1.0"), "pfasimplu-3.1.0-windows-x86_64.exe")

    def test_versiune_invalidata(self):
        for versiune in ("3.0", "3.0.1-beta", "../3.0.1"):
            with self.subTest(versiune=versiune), self.assertRaises(EroareActualizare):
                nume_asset(versiune)


class DetectieStandaloneTests(TestCase):
    def test_gaseste_executabilul_din_payload(self):
        radacina = Path(tempfile.mkdtemp(prefix="pfasimplu_detectie_"))
        executabil = radacina / "pfasimplu-3.0.0-linux-x86_64"
        executabil.write_bytes(b"EXE")
        python = radacina / "pycrucible_payload" / ".venv" / "bin" / "python"
        with (
            patch("utils.actualizare.sys.executable", str(python)),
            patch.dict(os.environ, {"PFASIMPLU_EXE_NAME": executabil.name}),
        ):
            self.assertTrue(este_standalone())
            self.assertEqual(calea_executabilului(), executabil)

    def test_fara_payload_nu_e_standalone(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(este_standalone())
            self.assertIsNone(calea_executabilului())


class DescarcaExecutabilTests(TestCase):
    def setUp(self):
        self.director = Path(tempfile.mkdtemp(prefix="pfasimplu_update_test_"))
        patcher = patch(
            "utils.actualizare._platforma", return_value=("linux", "x86_64")
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_extrage_doar_executabilul(self):
        raspuns = RaspunsFals(arhiva_cu("pfasimplu-3.0.1-linux-x86_64"))
        with patch("utils.actualizare.requests.get", return_value=raspuns):
            rezultat = descarca_executabil("3.0.1", self.director)
        self.assertEqual(rezultat.read_bytes(), b"EXE-FALS")
        self.assertFalse((self.director / "actualizare.zip").exists())

    def test_refuza_arhiva_fara_executabilul_asteptat(self):
        raspuns = RaspunsFals(arhiva_cu("altceva.exe"))
        with (
            patch("utils.actualizare.requests.get", return_value=raspuns),
            self.assertRaises(EroareActualizare),
        ):
            descarca_executabil("3.0.1", self.director)


class ActualizeazaViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user@test.ro", password="parola-sigura-123"
        )
        self.url = reverse("setari-actualizeaza")

    def test_cer_login(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)

    @patch("setari.views.pregateste_actualizarea")
    @patch("setari.views.get_latest_app_version", return_value="3.0.0")
    def test_fara_versiune_noua_nu_instaleaza(self, _versiune, instaleaza):
        self.client.force_login(self.user)
        raspuns = self.client.post(self.url, follow=True)
        instaleaza.assert_not_called()
        self.assertContains(raspuns, "Nu exista o versiune noua de instalat.")

    @patch("setari.views.pregateste_actualizarea")
    @patch("setari.views.get_latest_app_version", return_value="3.0.1")
    def test_versiune_noua_afiseaza_mesajul(self, _versiune, instaleaza):
        instaleaza.return_value = "Versiunea V3.0.1 a fost descarcata."
        self.client.force_login(self.user)
        raspuns = self.client.post(self.url, follow=True)
        instaleaza.assert_called_once_with("3.0.1")
        self.assertContains(raspuns, "Versiunea V3.0.1 a fost descarcata.")

    @patch("utils.actualizare.calea_executabilului", return_value=None)
    @patch("setari.views.get_latest_app_version", return_value="3.0.1")
    def test_docker_refuza_inlocuirea(self, _versiune, _calea):
        self.client.force_login(self.user)
        raspuns = self.client.post(self.url, follow=True)
        self.assertContains(raspuns, "disponibila numai in versiunea standalone")
