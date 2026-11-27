"""Regresiune: switch-ul „Client UE” se preia din ultima factura a clientului
cand numele este ales din lista de sugestii."""

import datetime

import pytest
from conftest import TEST_YEAR
from helpers import completare_setari, emite_factura
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

NUME_CLIENT = "CLIENT AUTOMAT UE"
CIF_CLIENT = "RO12345678"
ADRESA_CLIENT = "STR. CLIENTULUI NR. 7, BUCURESTI"


def _iban(bban: str) -> str:
    """IBAN romanesc cu cifra de control calculata corect."""
    cifre = "".join(str(int(c, 36)) for c in bban + "RO00")
    check = 98 - int(cifre) % 97
    return f"RO{check:02d}{bban}"


def test_client_ue_se_completeaza_din_sugestii(page):
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

    data_emitere = datetime.date(TEST_YEAR, 1, 5)
    produse = [
        {
            "nume": "Servicii de consultanta",
            "cod_unitate": "HUR",
            "unitati": 1,
            "pret": "100",
        }
    ]

    # Prima factura a clientului, fara Client UE.
    emite_factura(
        page,
        nume_client=NUME_CLIENT,
        cif_client=CIF_CLIENT,
        numar=1,
        data_emitere=data_emitere,
        data_scadenta=data_emitere + datetime.timedelta(days=30),
        produse=produse,
        adresa=ADRESA_CLIENT,
    )

    # A doua factura, cu Client UE bifat pentru acelasi client.
    emite_factura(
        page,
        nume_client=NUME_CLIENT,
        cif_client=CIF_CLIENT,
        numar=2,
        data_emitere=data_emitere + datetime.timedelta(days=1),
        data_scadenta=data_emitere + datetime.timedelta(days=31),
        produse=produse,
        adresa=ADRESA_CLIENT,
        client_ue=True,
    )

    # Factura noua: alegem clientul din sugestii si verificam ca toate
    # campurile, inclusiv switch-ul Client UE, au fost preluate.
    page.goto("/facturi/")
    page.fill("#id_nume", NUME_CLIENT)
    suggestie = page.locator("ul.suggestions li").filter(has_text=NUME_CLIENT).first
    expect(suggestie).to_be_visible(timeout=10_000)
    suggestie.click()

    expect(page.locator("#id_client_ue")).to_be_checked()
    expect(page.locator("#id_cif")).to_have_value(CIF_CLIENT)
    expect(page.locator("#id_adresa")).to_have_value(ADRESA_CLIENT)
