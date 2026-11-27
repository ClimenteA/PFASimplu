"""Filtrul „Incasari din UE (TVA)" si descarcarea D390 din pagina Incasari."""

import datetime
import io
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from conftest import LAST_MONTH, TEST_YEAR
from helpers import completare_setari, emite_factura, incasare_din_factura
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

NUME_CLIENT_UE = "CLIENT UE D390"
CIF_CLIENT_UE = "ATU77164426"
NUME_CLIENT_UE_2 = "DEMO GMBH"
CIF_CLIENT_UE_2 = "DE123456789"
NUME_CLIENT_UE_3 = "ITALIA SRL"
CIF_CLIENT_UE_3 = "IT12345678901"


def _iban(bban: str) -> str:
    cifre = "".join(str(int(c, 36)) for c in bban + "RO00")
    check = 98 - int(cifre) % 97
    return f"RO{check:02d}{bban}"


def test_incasari_ue_filtru_si_d390(page):
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

    zi = datetime.date(TEST_YEAR, LAST_MONTH, 2)
    emite_factura(
        page,
        nume_client=NUME_CLIENT_UE,
        cif_client=CIF_CLIENT_UE,
        numar=999,
        serie="UE",
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        tip_factura="factura-engleza",
        valuta="RON",
        client_ue=True,
        produse=[{"nume": "Consultanta UE", "unitati": 1, "pret": 100}],
    )
    incasare_din_factura(page, "UE", 999, zi)

    # Incasari din UE pentru alti clienti VIES (Germania si Italia), in aceeasi
    # luna de raportare, ca sa acoperim mai multi operatori intracomunitari.
    emite_factura(
        page,
        nume_client=NUME_CLIENT_UE_2,
        cif_client=CIF_CLIENT_UE_2,
        numar=1000,
        serie="UE",
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        tip_factura="factura-engleza",
        valuta="RON",
        client_ue=True,
        produse=[{"nume": "Consultanta UE DE", "unitati": 1, "pret": 80}],
    )
    incasare_din_factura(page, "UE", 1000, zi)
    emite_factura(
        page,
        nume_client=NUME_CLIENT_UE_3,
        cif_client=CIF_CLIENT_UE_3,
        numar=1001,
        serie="UE",
        data_emitere=zi,
        data_scadenta=zi + datetime.timedelta(days=30),
        tip_factura="factura-engleza",
        valuta="RON",
        client_ue=True,
        produse=[{"nume": "Consultanta UE IT", "unitati": 1, "pret": 50}],
    )
    incasare_din_factura(page, "UE", 1001, zi)

    page.goto(f"/incasari/?ue=1&anul_ue={TEST_YEAR}&luna_ue={LAST_MONTH}")

    expect(page.locator("#filtru-ue")).to_have_value(str(LAST_MONTH))
    # Filtrul applied in tabelul de mai jos (jurnalul de vanzari).
    randuri = page.locator("#tabel-incasari tbody tr")
    expect(randuri.first).to_be_visible()
    assert randuri.count() == 3
    text = "\n".join(randuri.nth(i).inner_text() for i in range(randuri.count()))
    for nume in (NUME_CLIENT_UE, NUME_CLIENT_UE_2, NUME_CLIENT_UE_3):
        assert nume in text
    for i in range(randuri.count()):
        assert randuri.nth(i).locator("td").nth(2).inner_text().strip() == "Da"

    # Coloana UE din tabelul principal si din formularul de cautare.
    expect(page.locator("#tabel-incasari thead th").nth(2)).to_have_text("VIES")
    page.select_option("#cautare select[name='coloana']", "ue")
    page.fill("#cautare input[name='cauta']", "UE")
    page.get_by_role("button", name="Cauta").click()

    with page.expect_download() as download_info:
        page.locator("#filtru-incasari-ue").get_by_role(
            "button", name="Descarca"
        ).click()
    download = download_info.value
    assert download.suggested_filename == f"D390_{TEST_YEAR}_{LAST_MONTH:02d}.zip"

    zip_path = Path(tempfile.mkdtemp()) / download.suggested_filename
    download.save_as(zip_path)
    with ZipFile(zip_path) as zf:
        nume = zf.namelist()
        assert f"TVA-52937756/D390_{TEST_YEAR}_{LAST_MONTH:02d}.md" in nume
        assert f"TVA-52937756/Jurnal_vanzari_{TEST_YEAR}_{LAST_MONTH:02d}.xlsx" in nume
        assert any(n.startswith("TVA-52937756/facturi/") for n in nume)
        assert not any("D301" in n for n in nume)
        md = zf.read(f"TVA-52937756/D390_{TEST_YEAR}_{LAST_MONTH:02d}.md").decode()
        assert "P - Prestari intracomunitare de servicii" in md
        assert "| **P - Prestari intracomunitare de servicii** | **`230`** |" in md
        assert "U77164426" in md
        assert "123456789" in md
        assert "12345678901" in md

    # Jurnalul de vanzari din pagina Registre, langa cel de cumparaturi.
    page.goto(f"/registre/?anul={TEST_YEAR}")
    page.get_by_role("button", name="Jurnal Vanzari").click()
    tab = page.locator("div[x-show=\"active == 'jurnale-vanzari'\"]")
    expect(tab).to_be_visible()
    randuri = tab.locator("tbody tr")
    expect(randuri.first).to_be_visible()
    text = "\n".join(randuri.nth(i).inner_text() for i in range(randuri.count()))
    for numar in ("UE-999", "UE-1000", "UE-1001"):
        assert numar in text
    with page.expect_download() as download_info:
        tab.locator("a[href*='filetype=XLSX'] i").click()
    assert download_info.value.suggested_filename == (
        f"jurnal_vanzari_{TEST_YEAR}.xlsx"
    )

    # Exportul anual din Setari contine si Jurnalul de vanzari.
    page.goto("/setari/")
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Exporta datele din aplicatie").click()
    download = download_info.value
    export_path = Path(tempfile.mkdtemp()) / download.suggested_filename
    download.save_as(export_path)
    with ZipFile(export_path) as zf:
        nume_jurnal = f"Jurnal_Vanzari_{TEST_YEAR}.xlsx"
        assert nume_jurnal in zf.namelist()
        df = pd.read_excel(io.BytesIO(zf.read(nume_jurnal)))
        assert "Baza impozitare" in df.columns
        assert any("UE-999" in str(nr) for nr in df["Document Numar"])
