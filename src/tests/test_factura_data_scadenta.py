"""Regresiuni pentru formularul de factura: scadenta automata si starea campurilor."""

import datetime

import pytest
from conftest import TODAY
from helpers import assert_error, completare_setari, emite_factura
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def _iban(bban: str) -> str:
    """IBAN romanesc cu cifra de control calculata corect."""
    cifre = "".join(str(int(c, 36)) for c in bban + "RO00")
    check = 98 - int(cifre) % 97
    return f"RO{check:02d}{bban}"


def _setari(page):
    completare_setari(
        page,
        nume="PFA TEST",
        cif="RO87654321",
        nr_reg_com="F22/123/2020",
        localitate="RO-IS, jud. Iasi, Iasi",
        adresa="Strada Testului 1",
        email="test@example.com",
        telefon="0700000000",
        iban_ron=_iban("BTRL01234567890123456789"),
        iban_eur=_iban("BTRL01234567890123456790"),
        cod_tva_intracomunitar="52937756",
        iban_trezorerie="RO41TREZ40620A100101XTVA",
    )


def test_scadenta_se_recalculeaza_la_30_de_zile(page):
    _setari(page)
    page.goto("/facturi/")
    expect(page.locator("#factura-form")).to_be_visible()
    page.locator("#mai-mult-switch").check()

    zi = TODAY - datetime.timedelta(days=60)
    page.fill("#id_data_emitere", zi.isoformat())
    page.locator("#id_data_emitere").dispatch_event("change")
    expect(page.locator("#id_data_scadenta")).to_have_value(
        (zi + datetime.timedelta(days=30)).isoformat()
    )

    # O a doua schimbare recalculeaza de la zero, nu aduna peste scadenta veche.
    zi_noua = TODAY - datetime.timedelta(days=10)
    page.fill("#id_data_emitere", zi_noua.isoformat())
    page.locator("#id_data_emitere").dispatch_event("change")
    expect(page.locator("#id_data_scadenta")).to_have_value(
        (zi_noua + datetime.timedelta(days=30)).isoformat()
    )


def test_localitatea_ramane_dezactivata_dupa_eroare(page):
    _setari(page)
    zi = TODAY - datetime.timedelta(days=60)

    emite_factura(
        page,
        nume_client="CLIENT GERMAN",
        cif_client="12345678",  # fara prefix UE -> eroare de validare
        serie="GER",
        numar=1,
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        produse=[{"nume": "Consultanta", "unitati": 1, "pret": "100"}],
        tip_factura="factura-germana",
        client_ue=True,
        salvare_asteptata=False,
    )

    assert_error(page, "Nu am putut inregistra factura!")
    page.locator("dialog[open]").get_by_role("button", name="Close").click()

    expect(page.locator("#id_tip_factura")).to_have_value("factura-germana")
    expect(page.locator("#alege-localitatea")).to_be_disabled()
    expect(page.locator("#id_nume")).to_have_value("CLIENT GERMAN")
    expect(page.locator("#id_data_emitere")).to_have_value(zi.isoformat())
