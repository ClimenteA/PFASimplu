"""Regresiune: factura cu „Client UE VIES” cere cod TVA cu prefix de tara UE."""

import datetime

import pytest
from conftest import TEST_YEAR
from helpers import assert_error, completare_setari, emite_factura
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def _iban(bban: str) -> str:
    """IBAN romanesc cu cifra de control calculata corect."""
    cifre = "".join(str(int(c, 36)) for c in bban + "RO00")
    check = 98 - int(cifre) % 97
    return f"RO{check:02d}{bban}"


def test_client_ue_cu_cif_romanesc_nu_se_salveaza(page):
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

    zi = datetime.date(TEST_YEAR, 1, 5)
    emite_factura(
        page,
        nume_client="CLIENT RO",
        cif_client="RO12345678",
        serie="VAL",
        numar=1,
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        produse=[{"nume": "Consultanta", "unitati": 1, "pret": "100"}],
        client_ue=True,
        salvare_asteptata=False,
    )

    assert_error(page, "Nu am putut inregistra factura!")
    expect(page.locator("label[for='id_cif'] .errorlist")).to_contain_text(
        "prefixul tarii UE"
    )
    page.locator("dialog[open]").get_by_role("button", name="Close").click()

    # Campurile completate inainte de submit raman in formular dupa eroare.
    expect(page.locator("#id_nume")).to_have_value("CLIENT RO")
    expect(page.locator("#id_cif")).to_have_value("RO12345678")
    expect(page.locator("#id_serie")).to_have_value("VAL")
    expect(page.locator("#id_numar")).to_have_value("1")
    expect(page.locator("#id_adresa")).to_have_value("STR. TESTULUI NR. 1, BUCURESTI")
    expect(page.locator("#id_data_emitere")).to_have_value(zi.isoformat())
    expect(page.locator("#id_data_scadenta")).to_have_value(
        (zi + datetime.timedelta(days=30)).isoformat()
    )
    expect(page.locator("#id_tip_factura")).to_have_value("factura-engleza")
    expect(page.locator("#id_valuta")).to_have_value("EUR")
    expect(
        page.locator("form#factura-form article input[type='text']").first
    ).to_have_value("Consultanta")
    expect(page.locator("#id_total_de_plata")).to_have_value("100.00")

    # Factura respinsa nu ajunge in tabel (filtram dupa serie, pe toate paginile).
    page.locator("#cautare input[name='cauta']").fill("VAL")
    page.select_option("#cautare select[name='coloana']", "serie")
    page.get_by_role("button", name="Cauta").click()
    expect(page.locator("#tabel-facturi tbody tr")).to_have_count(0)

    # Acelasi client, fara bifa „Client UE VIES”, se salveaza normal.
    emite_factura(
        page,
        nume_client="CLIENT RO",
        cif_client="RO12345678",
        serie="VAL",
        numar=2,
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        produse=[{"nume": "Consultanta", "unitati": 1, "pret": "100"}],
    )
    expect(page.locator("#tabel-facturi tbody tr").first).to_contain_text("VAL")
