"""Helper-e Playwright pentru formularele PFASimplu (Alpine.js / Pico CSS)."""

import re
import sys
from decimal import Decimal
from pathlib import Path

# pytest pune in sys.path doar directorul tests/ (nu si src/), asa ca adaugam
# explicit sursele pentru a importa utilitarul de calcul cu Decimal.
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conftest import FILES_DIR
from playwright.sync_api import Page, expect

from utils.decimale import D, rotund2, suma

# Cota standard de TVA folosita de aplicatie la taxarea inversa (art. 291).
COTA_TVA = 0.21

# Codurile scurte stocate in DB pentru deductibilitate (etichetele afisate
# sunt textul descriptiv din models.py).
MIJLOC_FIX = "MIJLOC_FIX"
DEDUCTIBIL_INTEGRAL = "INTEGRAL"
OBIECT_INVENTAR = "INVENTAR"
AUTO_UTILITATI_50 = "AUTO_50"

TIP_ACHIZITIE_UE = "Servicii UE"
TIP_ACHIZITIE_NON_UE = "Servicii non-UE"

SURSA_ACTIVITATE = "ACTIVITATE"
SURSA_ALTELE = "ALTE"


def assert_saved(page: Page):
    """Verifica dialogul de succes aparut dupa salvarea unui formular."""
    dialog = page.locator("dialog article").first
    expect(dialog).to_be_visible(timeout=15_000)
    expect(dialog).to_contain_text("Datele au fost salvate!")


def assert_error(page: Page, text: str | None = None):
    dialog = page.locator("dialog article").first
    expect(dialog).to_be_visible(timeout=15_000)
    expect(dialog).to_contain_text("Eroare")
    if text:
        expect(dialog).to_contain_text(text)


def pdf_justificativ(nume: str) -> str:
    """Creeaza un PDF minimal valid, folosit ca document justificativ."""
    path = FILES_DIR / f"{nume}.pdf"
    if not path.exists():
        path.write_bytes(
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
            b"trailer<</Root 1 0 R>>\n%%EOF"
        )
    return str(path)


def completare_setari(
    page: Page,
    *,
    nume: str,
    cif: str,
    nr_reg_com: str,
    localitate: str,
    adresa: str,
    email: str,
    telefon: str,
    iban_ron: str,
    iban_eur: str,
    cod_tva_intracomunitar: str,
    iban_trezorerie: str,
    caen_principal: str = "6201",
):
    """Completeaza formularul din pagina Setari, inclusiv conturile IBAN
    multiple (widget Alpine) si sectiunea TVA intracomunitar (D301/D390)."""
    page.goto("/setari/")

    page.fill("#id_nume", nume)
    page.fill("#id_cif", cif)
    page.fill("#id_nr_reg_com", nr_reg_com)
    page.fill("input[name='localitate']", localitate)
    page.fill("#id_adresa", adresa)
    page.fill("#id_email", email)
    page.fill("#id_telefon", telefon)
    page.fill("#id_caen_principal", caen_principal)

    # Cont IBAN RON (randul initial) + cont EUR (rand adaugat din buton).
    page.fill("input[aria-label='IBAN'] >> nth=0", iban_ron)
    page.get_by_role("button", name="Adauga cont IBAN").click()
    page.locator("select[aria-label='Valuta cont'] >> nth=1").select_option("EUR")
    page.fill("input[aria-label='IBAN'] >> nth=1", iban_eur)

    # Sectiunea TVA intracomunitar (cod special art. 317 + IBAN trezorerie).
    page.get_by_role("button", name="TVA intracomunitar (D301/D390)").click()
    page.fill("#id_cod_tva_intracomunitar", cod_tva_intracomunitar)
    page.fill("#id_cont_iban_trezoreria", iban_trezorerie)

    page.get_by_role("button", name="Salveaza datele PFA").click()
    assert_saved(page)


def emite_factura(
    page: Page,
    *,
    nume_client: str,
    cif_client: str,
    numar: int,
    data_emitere,
    data_scadenta,
    produse: list[dict],
    tip_factura: str = "factura-engleza",
    valuta: str = "EUR",
    tip_tranzactie: str = "BANCAR",
    serie: str = "PFT",
    adresa: str = "STR. TESTULUI NR. 1, BUCURESTI",
    localitate: str = "",
    nota: str = "",
) -> Decimal:
    """Emite o factura prin formularul Alpine din pagina Facturi.

    `produse` = [{nume, cod_unitate, unitati, pret}, ...].
    Intoarce totalul de plata (calculat de formular).
    """
    page.goto("/facturi/")
    # Fara Setari completate, pagina Facturi redirecteaza la /setari/.
    page.wait_for_url("**/facturi/")
    expect(page.locator("#factura-form")).to_be_visible()

    page.fill("#id_nume", nume_client)
    page.fill("#id_cif", cif_client)
    page.fill("#id_serie", serie)
    page.fill("#id_numar", str(numar))
    page.select_option("#id_tip_factura", tip_factura)
    page.select_option("#id_tip_tranzactie", tip_tranzactie)
    # Valuta e dezactivata pentru e-factura/factura romana (mereu RON);
    # la submit formularul o reactiveaza oricum (vezi handleSubmit).
    if tip_factura in ("e-factura", "factura-romana"):
        expect(page.locator("#id_valuta")).to_have_value("RON")
    else:
        page.select_option("#id_valuta", valuta)
    if localitate:
        page.fill("#alege-localitatea", localitate)
    page.fill("#id_adresa", adresa)

    # Switch-ul "Client UE" e unchecked by default.
    expect(page.locator("#id_client_ue")).not_to_be_checked()

    # Campurile de date sunt in sectiunea "Mai mult".
    page.locator("#mai-mult-switch").check()
    page.fill("#id_data_emitere", data_emitere.isoformat())
    page.fill("#id_data_scadenta", data_scadenta.isoformat())
    if nota:
        page.fill("#id_nota", nota)

    for idx, produs in enumerate(produse):
        articol = page.locator("form#factura-form article").nth(idx)
        articol.locator("input[type='text']").fill(produs["nume"])
        articol.locator("select").select_option(produs.get("cod_unitate", "HUR"))
        articol.locator("input[type='number']").nth(0).fill(str(produs["unitati"]))
        articol.locator("input[type='number']").nth(1).fill(str(produs["pret"]))
        if idx < len(produse) - 1:
            page.get_by_role("button", name="Adauga", exact=True).click()

    page.get_by_role("button", name="Creeaza factura").click()
    assert_saved(page)

    # Calculul se face cu Decimal (4 zecimale in intermediar, ROUND_HALF_UP la
    # 2 zecimale pentru totalul final), ca in formularul din src/templates/facturi.html.
    total = suma([D(int(p["unitati"])) * D(p["pret"]) for p in produse])
    return rotund2(total)


def incasare_din_factura(page: Page, serie: str, numar: int, data_incasarii) -> None:
    """Incasare pornita din pagina Facturi (butonul 💳 'Incasata').

    Formularul vine precompletat din factura (nume incasare, suma, valuta,
    tip tranzactie, PDF atasat automat); completam doar data incasarii.
    """
    page.goto("/facturi/")
    page.wait_for_url("**/facturi/")
    # Serie si numar sunt in celule separate; potrivim exact ca sa nu
    # confundam factura 11 cu 111 etc.
    rand = (
        page.locator("#tabel-facturi tbody tr")
        .filter(
            has=page.locator("td:nth-child(8)").filter(
                has_text=re.compile(f"^{serie}$")
            )
        )
        .filter(
            has=page.locator("td:nth-child(9)").filter(
                has_text=re.compile(f"^{numar}$")
            )
        )
        .first
    )
    # Click pe iconita din link: centrul bounding box-ului unui <a> inline
    # poate pica pe spatiul dintre linii, unde alt element intercepteaza.
    rand.locator("a[href*='factura_id'] i").click()

    page.wait_for_url("**/incasari/?factura_id=*")
    expect(page.locator("#form-incasare")).to_be_visible()
    expect(page.locator("#id_nume_incasare")).to_have_value(re.compile(".+"))
    page.fill("#id_data_inserarii", data_incasarii.isoformat())
    page.get_by_role("button", name="Salveaza incasare").click()
    assert_saved(page)


def incasare_separata(
    page: Page,
    *,
    suma: float,
    data_incasarii,
    fisier: str,
    valuta: str = "RON",
    tip_tranzactie: str = "BANCAR",
    sursa_venit: str = SURSA_ACTIVITATE,
) -> None:
    """Incasare adaugata direct din formularul paginii Incasari."""
    page.goto("/incasari/")
    page.select_option("#id_sursa_venit", sursa_venit)
    page.fill("#id_suma", str(suma))
    page.select_option("#id_valuta", valuta)
    page.select_option("#id_tip_tranzactie", tip_tranzactie)
    page.fill("#id_data_inserarii", data_incasarii.isoformat())
    page.set_input_files("#id_fisier", fisier)
    page.get_by_role("button", name="Salveaza incasare").click()
    assert_saved(page)


def adauga_cheltuiala(
    page: Page,
    *,
    nume: str,
    suma: float,
    data_cheltuielii,
    fisier: str,
    deductibila: str = DEDUCTIBIL_INTEGRAL,
    valuta: str = "RON",
    tip_tranzactie: str = "BANCAR",
    tip_achizitie: str = "Romania",
    furnizor_denumire: str = "",
    furnizor_tara: str = "",
    furnizor_cod_fiscal: str = "",
    numar_factura: str = "",
    data_facturii=None,
    cod_de_clasificare: str = "",
    ani_amortizare: int | None = None,
    data_punerii_in_functiune=None,
) -> None:
    """Adauga o cheltuiala (obisnuita, obiect de inventar, mijloc fix sau
    servicii UE/non-UE cu taxare inversa) din formularul paginii Cheltuieli."""
    page.goto("/cheltuieli/")

    page.select_option("#id_deductibila", deductibila)
    page.fill("#id_nume_cheltuiala", nume)
    page.fill("#id_suma", str(suma))
    page.select_option("#id_valuta", valuta)
    page.select_option("#id_tip_tranzactie", tip_tranzactie)
    page.fill("#id_data_inserarii", data_cheltuielii.isoformat())

    if deductibila == MIJLOC_FIX:
        page.fill("#id_cod_de_clasificare", cod_de_clasificare)
        if ani_amortizare:
            page.fill("#id_ani_amortizare", str(ani_amortizare))
        page.fill(
            "#id_data_punerii_in_functiune", data_punerii_in_functiune.isoformat()
        )

    if tip_achizitie != "Romania":
        page.select_option("#id_tip_achizitie", tip_achizitie)
        page.fill("#id_furnizor_denumire", furnizor_denumire)
        page.select_option("#id_furnizor_tara", furnizor_tara)
        if furnizor_cod_fiscal:
            page.fill("#id_furnizor_cod_fiscal", furnizor_cod_fiscal)
        page.fill("#id_numar_factura", numar_factura)
        if data_facturii:
            page.fill("#id_data_facturii", data_facturii.isoformat())

    page.set_input_files("#id_fisier", fisier)
    page.get_by_role("button", name="Salveaza cheltuiala").click()
    assert_saved(page)


def rand_cheltuiala(page: Page, nume: str):
    """Randul din tabelul de cheltuieli pentru o cheltuiala cu numele dat.

    Tabelul afiseaza 20 de randuri pe pagina, asa ca cautam in toate paginile.
    """
    page.goto("/cheltuieli/")
    text_paginare = page.locator(".pagination p").inner_text()
    numar_pagini = int(re.search(r"din (\d+)", text_paginare).group(1))
    for nr_pagina in range(1, numar_pagini + 1):
        page.goto(f"/cheltuieli/?page={nr_pagina}#tabel-cheltuieli")
        rand = page.locator("#tabel-cheltuieli tbody tr").filter(has_text=nume).first
        if rand.count():
            return rand
    return page.locator("#tabel-cheltuieli tbody tr").filter(has_text=nume).first


def cell_float(row, index: int) -> float:
    # Celulele pot contine si emoji (ex. "90.92 🇪🇺" la TVA):
    # pastram doar primul numar din text.
    text = row.locator("td").nth(index).inner_text().strip()
    match = re.search(r"-?\d+(?:[.,]\d+)?", text)
    assert match, f"Celula nu contine un numar: {text!r}"
    return float(match.group(0).replace(",", "."))
