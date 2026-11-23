"""Teste pentru modul multi-user (PFASIMPLU_MULTI_USER=1):
login/inregistrare cu email + parola si izolarea datelor per utilizator.
"""

import datetime
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cheltuieli.models import CheltuialaModel
from setari.models import SetariModel
from utils.files import get_save_path
from utils.multiuser import get_current_user


MEDIA_TEST = tempfile.mkdtemp(prefix="pfasimplu_test_multiuser_media_")


def creeaza_utilizator(email="user@test.ro", parola="parola-sigura-123"):
    return User.objects.create_user(username=email, email=email, password=parola)


def creeaza_cheltuiala(user, **kwargs):
    defaults = dict(
        user=user,
        nume_cheltuiala="Consumabile",
        suma=100.0,
        valuta="RON",
        data_inserarii=datetime.date(2026, 1, 15),
        fisier=SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
    )
    defaults.update(kwargs)
    return CheltuialaModel.objects.create(**defaults)


@override_settings(MULTI_USER=True, MEDIA_ROOT=MEDIA_TEST)
class AutentificareTests(TestCase):

    def test_paginile_cer_login(self):
        for url in ("/", "/registre/", "/cheltuieli/", "/incasari/", "/setari/", "/documente/", "/facturi/", "/inventar/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn(reverse("login"), response["Location"], url)

    def test_inregistrare_cu_email(self):
        response = self.client.post(reverse("inregistrare"), {
            "email": "Nou@Test.ro",
            "password1": "parola-sigura-123",
            "password2": "parola-sigura-123",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="nou@test.ro")
        self.assertEqual(user.email, "nou@test.ro")
        # Utilizatorul e autentificat automat dupa inregistrare.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_inregistrare_email_duplicat(self):
        creeaza_utilizator()
        response = self.client.post(reverse("inregistrare"), {
            "email": "user@test.ro",
            "password1": "parola-sigura-123",
            "password2": "parola-sigura-123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_inregistrare_parola_slaba(self):
        response = self.client.post(reverse("inregistrare"), {
            "email": "nou@test.ro",
            "password1": "12345678",
            "password2": "12345678",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nou@test.ro").exists())

    def test_login_cu_email_si_parola(self):
        creeaza_utilizator()
        response = self.client.post(reverse("login"), {
            "username": "user@test.ro",
            "password": "parola-sigura-123",
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_login_parola_gresita(self):
        creeaza_utilizator()
        response = self.client.post(reverse("login"), {
            "username": "user@test.ro",
            "password": "gresita",
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        creeaza_utilizator()
        self.client.login(username="user@test.ro", password="parola-sigura-123")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/")
        self.assertIn(reverse("login"), response["Location"])

    def test_next_doar_pe_gazda_curenta(self):
        creeaza_utilizator()
        response = self.client.post(reverse("login") + "?next=https://evil.example.com/", {
            "username": "user@test.ro",
            "password": "parola-sigura-123",
        })
        self.assertEqual(response["Location"], "/")


@override_settings(MULTI_USER=True, MEDIA_ROOT=MEDIA_TEST)
class IzolareDateTests(TestCase):

    def setUp(self):
        self.user1 = creeaza_utilizator("unu@test.ro")
        self.user2 = creeaza_utilizator("doi@test.ro")
        self.cheltuiala1 = creeaza_cheltuiala(self.user1, nume_cheltuiala="Cheltuiala user 1")
        self.cheltuiala2 = creeaza_cheltuiala(self.user2, nume_cheltuiala="Cheltuiala user 2")

    def test_lista_cheltuieli_doar_ale_mele(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.get(reverse("cheltuieli"))
        items = list(response.context["page_items"])
        self.assertEqual([c.pk for c in items], [self.cheltuiala1.pk])

    def test_editare_cheltuiala_altui_utilizator_404(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.get(reverse("cheltuieli"), {"id": self.cheltuiala2.pk})
        self.assertEqual(response.status_code, 404)

    def test_stergere_cheltuiala_altui_utilizator_404(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.get(reverse("cheltuieli"), {"delete_id": self.cheltuiala2.pk})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CheltuialaModel.objects.filter(pk=self.cheltuiala2.pk).exists())

    def test_setari_per_utilizator(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.get(reverse("setari"))
        self.assertIsNone(response.context["setari_form"].instance.pk)

    def test_salvare_ataseaza_utilizatorul_curent(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.post(reverse("cheltuieli"), {
            "nume_cheltuiala": "Noua",
            "deductibila": "Deductibila integral",
            "suma": "50.00",
            "valuta": "RON",
            "tip_tranzactie": "BANCAR",
            "tip_achizitie": "Romania",
            "data_inserarii": "2026-01-20",
            "fisier": SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
            "obiect_de_inventar": False,
            "mijloc_fix": False,
            "scos_din_uz": False,
        })
        self.assertEqual(response.status_code, 302)
        c = CheltuialaModel.objects.get(nume_cheltuiala="Noua")
        self.assertEqual(c.user, self.user1)

    def test_fisiere_in_folderul_utilizatorului(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        self.client.post(reverse("cheltuieli"), {
            "nume_cheltuiala": "Cu fisier",
            "deductibila": "Deductibila integral",
            "suma": "50.00",
            "valuta": "RON",
            "tip_tranzactie": "BANCAR",
            "tip_achizitie": "Romania",
            "data_inserarii": "2026-01-20",
            "fisier": SimpleUploadedFile("bon.pdf", b"%PDF-1.4 test"),
            "obiect_de_inventar": False,
            "mijloc_fix": False,
            "scos_din_uz": False,
        })
        c = CheltuialaModel.objects.get(nume_cheltuiala="Cu fisier")
        self.assertTrue(c.fisier.name.startswith(f"user_{self.user1.id}/"))

    def test_media_altui_utilizator_404(self):
        self.client.login(username="doi@test.ro", password="parola-sigura-123")
        response = self.client.get("/media/" + self.cheltuiala1.fisier.name)
        self.assertEqual(response.status_code, 404)

    def test_media_propriu_accesibil(self):
        self.client.login(username="unu@test.ro", password="parola-sigura-123")
        response = self.client.get("/media/" + self.cheltuiala1.fisier.name)
        self.assertEqual(response.status_code, 200)

    def test_media_fara_login_cere_autentificare(self):
        response = self.client.get("/media/" + self.cheltuiala1.fisier.name)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/conturi/login/", response["Location"])


@override_settings(MULTI_USER=True, ALLOW_REGISTRATION=False, MEDIA_ROOT=MEDIA_TEST)
class InregistrareBlocataTests(TestCase):
    """PFASIMPLU_ALLOW_REGISTRATION=0: fara conturi noi, login-ul merge."""

    def test_pagina_inregistrare_404(self):
        response = self.client.get(reverse("inregistrare"))
        self.assertEqual(response.status_code, 404)

    def test_post_inregistrare_404_fara_cont_nou(self):
        response = self.client.post(reverse("inregistrare"), {
            "email": "nou@test.ro",
            "password1": "parola-sigura-123",
            "password2": "parola-sigura-123",
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username="nou@test.ro").exists())

    def test_login_fara_link_inregistrare(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, "Inregistreaza-te")

    def test_utilizatorii_existenti_se_pot_autentifica(self):
        creeaza_utilizator()
        response = self.client.post(reverse("login"), {
            "username": "user@test.ro",
            "password": "parola-sigura-123",
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class DesktopImplicitTests(TestCase):
    """Fara PFASIMPLU_MULTI_USER aplicatia ramane fara login, ca pana acum."""

    def test_pagini_fara_login(self):
        for url in ("/", "/cheltuieli/", "/setari/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_login_redirecteaza_spre_aplicatie(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_cheltuiala_fara_utilizator(self):
        c = creeaza_cheltuiala(None)
        self.assertIsNone(c.user)
        self.assertFalse(c.fisier.name.startswith("user_"))
