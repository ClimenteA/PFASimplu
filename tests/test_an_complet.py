"""Scenariu end-to-end pe un an intreg (anul curent).

Ordinea fluxului, asa cum lucreaza un utilizator real:
    1. completare Setari (date PFA, conturi IBAN, cod TVA art. 317);
    2. pentru fiecare luna din an (pana in luna curenta, aplicatia nu accepta
       date din viitor):
         - emitere facturi (e-factura B2B in Romania + facturi externe EUR);
         - incasari din facturi (butonul "Incasata") si incasari separate,
           completate direct in formularul din Incasari (max. 5/luna);
         - cheltuieli diverse: consumabile, servicii, obiecte de inventar,
           auto/utilitati 50%, mijloace fixe (2-3 pe an) si servicii UE/non-UE
           cu taxare inversa pentru TVA (D301/D390) - max. 10/luna;
    3. verificari finale: venit total sub 395.000 RON, TVA autolichidata
       calculata corect, amortizari mijloace fixe.

Datele sunt generate cu Faker (locale ro_RO). Baza de date de test ramane in
tests/.runtime/test.db pentru inspectie ulterioara.
"""

import datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect

from conftest import LAST_MONTH, TEST_YEAR, VENIT_MAX_RON, fake, luna_zi
from helpers import (
    AUTO_UTILITATI_50,
    COTA_TVA,
    MIJLOC_FIX,
    OBIECT_INVENTAR,
    SURSA_ACTIVITATE,
    SURSA_ALTELE,
    TIP_ACHIZITIE_NON_UE,
    TIP_ACHIZITIE_UE,
    adauga_cheltuiala,
    cell_float,
    completare_setari,
    emite_factura,
    incasare_din_factura,
    incasare_separata,
    pdf_justificativ,
    rand_cheltuiala,
)

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Constante scenariu
# ---------------------------------------------------------------------------

# IBAN trezorerie valid (cifra de control corecta) pentru plata TVA prin D301.
IBAN_TREZORERIE = "RO41TREZ40620A100101XTVA"

# Furnizori de servicii externi, refolositi in mai multe luni (typeahead).
FURNIZORI_UE = [
    ("CORTECS GMBH", "DE", "DE815293774"),
    ("OVH SAS", "FR", "FR22424761419"),
    ("HETZNER ONLINE GMBH", "DE", "DE812871812"),
]
FURNIZORI_NON_UE = [
    ("GOOGLE LLC", "US", "27-0805829"),
    ("CLOUDFLARE INC", "US", "26-2938475"),
    ("GITHUB INC", "US", "20-8703069"),
]

# Mijloace fixe: 3 pe an, puse in functiune in lunile 1, 5 si 9 (sau mai
# devreme daca anul curent nu a ajuns inca acolo).
MIJLOACE_FIXE = [
    {
        "luna": 1,
        "nume": "Laptop Dell Latitude 7450",
        "cod": "2.2.9.",
        "ani": 3,
        "suma": (6500, 9500),
    },
    {
        "luna": 5,
        "nume": "Birou reglabil electric + scaun ergonomic",
        "cod": "3.1.1.",
        "ani": 10,
        "suma": (5200, 7000),
    },
    {
        "luna": 9,
        "nume": "Imprimanta laser multifunctionala Brother",
        "cod": "2.2.9.",
        "ani": 3,
        "suma": (5100, 6500),
    },
]

CHELTUIELI_INTEGRALE = [
    "Abonament internet fibra",
    "Abonament telefonie mobila",
    "Consumabile birou (hartie, toner)",
    "Licenta software contabilitate",
    "Abonament cloud hosting",
    "Servicii marketing online",
    "Comisioane bancare",
    "Abonament Adobe Creative Cloud",
]
CHELTUIELI_INVENTAR = [
    "Mouse wireless Logitech MX",
    "Tastatura mecanica",
    "Monitor portabil USB-C",
    "Casti cu anulare a zgomotului",
]


def _iban(bban: str) -> str:
    """IBAN romanesc cu cifra de control calculata corect."""
    cifre = "".join(str(int(c, 36)) for c in bban + "RO00")
    check = 98 - int(cifre) % 97
    return f"RO{check:02d}{bban}"


def _luna_mijloc_fix(luna_planificata: int) -> int:
    """Mijloacele fixe trebuie puse in functiune in trecut (fara date din
    viitor); daca luna planificata nu a venit inca, le devansam."""
    return min(luna_planificata, LAST_MONTH)


@pytest.fixture(scope="module")
def date_pfa():
    """Datele PFA-ului generate cu Faker, folosite in tot scenariul."""
    return {
        "nume": f"{fake.first_name()} {fake.last_name()} PFA",
        "cif": f"RO{fake.random_number(digits=8, fix_len=True)}",
        "nr_reg_com": f"F{fake.random_int(10, 52)}/{fake.random_int(100, 9999)}/2020",
        "localitate": "RO-IS, jud. Iasi, Iasi",
        "adresa": f"Str. {fake.street_name()} nr. {fake.random_int(1, 120)}",
        "email": fake.email(),
        "telefon": f"07{fake.random_number(digits=8, fix_len=True)}",
        "iban_ron": _iban("BTRL" + fake.numerify("#" * 20)),
        "iban_eur": _iban("BTRL" + fake.numerify("#" * 20)),
        "cod_tva_intracomunitar": str(fake.random_number(digits=8, fix_len=True)),
    }


# ---------------------------------------------------------------------------
# 1. Setari
# ---------------------------------------------------------------------------


def test_01_setari(page, date_pfa):
    completare_setari(page, iban_trezorerie=IBAN_TREZORERIE, **date_pfa)

    # Datele persista: reincarcam pagina si verificam valorile salvate.
    page.goto("/setari/")
    expect(page.locator("#id_nume")).to_have_value(date_pfa["nume"])
    expect(page.locator("#id_cif")).to_have_value(date_pfa["cif"])
    expect(page.locator("#id_cont_iban_trezoreria")).to_have_value(IBAN_TREZORERIE)
    expect(page.locator("input[aria-label='IBAN'] >> nth=0")).to_have_value(
        date_pfa["iban_ron"]
    )
    expect(page.locator("input[aria-label='IBAN'] >> nth=1")).to_have_value(
        date_pfa["iban_eur"]
    )


# ---------------------------------------------------------------------------
# 2. Facturi -> Incasari (din factura si separat), luna cu luna
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("luna", range(1, LAST_MONTH + 1))
def test_02_facturi_si_incasari(page, db, luna, date_pfa):
    buget_luna = (VENIT_MAX_RON - 45_000) / 12  # ~29k RON/luna, sub plafon

    # --- Factura 1: e-factura B2B in Romania (RON) -------------------------
    zi_emitere = luna_zi(TEST_YEAR, luna, max_day=20)
    total_ron = round(fake.random_int(4000, 9000) + fake.random_int(0, 99) / 100, 2)
    nume_client_ro = fake.company().upper()
    numar_ro = luna * 10 + 1
    emite_factura(
        page,
        nume_client=nume_client_ro,
        cif_client=f"RO{fake.random_number(digits=8, fix_len=True)}",
        numar=numar_ro,
        data_emitere=zi_emitere,
        data_scadenta=zi_emitere + datetime.timedelta(days=30),
        tip_factura="e-factura",
        valuta="RON",
        localitate="RO-CJ, jud. Cluj, Cluj-Napoca",
        adresa=f"STR. EXEMPLULUI NR. {fake.random_int(1, 90)}, CLUJ-NAPOCA",
        produse=[
            {
                "nume": "Servicii dezvoltare software",
                "unitati": 1,
                "pret": total_ron,
            }
        ],
        nota=f"Contract servicii {fake.bothify('CTR-####-??').upper()}",
    )

    # --- Factura 2: client extern, in EUR ----------------------------------
    unitati = fake.random_int(8, 32)
    pret_ora = fake.random_int(30, 60)
    numar_eu = luna * 10 + 2
    emite_factura(
        page,
        nume_client=fake.company().upper(),
        cif_client=fake.bothify("??#########").upper(),
        numar=numar_eu,
        data_emitere=zi_emitere,
        data_scadenta=zi_emitere + datetime.timedelta(days=30),
        tip_factura="factura-engleza",
        valuta="EUR",
        produse=[
            {
                "nume": "Software engineering services",
                "unitati": unitati,
                "pret": pret_ora,
            }
        ],
    )

    # --- Incasare 1: din factura RON (butonul "Incasata") ------------------
    zi_incasare_ro = max(zi_emitere, luna_zi(TEST_YEAR, luna))
    incasare_din_factura(page, "PFT", numar_ro, zi_incasare_ro)

    # --- Incasare 2: din factura EUR ---------------------------------------
    zi_incasare_eu = max(zi_emitere, luna_zi(TEST_YEAR, luna))
    incasare_din_factura(page, "PFT", numar_eu, zi_incasare_eu)

    # --- Incasari 3-5: separat, din formularul paginii Incasari ------------
    total_luna_ron = (
        db.execute(
            "SELECT COALESCE(SUM(suma_in_ron), 0) FROM incasari_incasarimodel "
            "WHERE data_inserarii LIKE ?",
            (f"{TEST_YEAR}-{luna:02d}%",),
        ).fetchone()[0]
    )
    ramas = buget_luna - total_luna_ron
    nr_separate = fake.random_int(1, 3)  # total max. 5 incasari/luna
    for i in range(nr_separate):
        if ramas < 500:
            break
        suma = round(min(ramas / (nr_separate - i), fake.random_int(300, 3500)), 2)
        incasare_separata(
            page,
            suma=suma,
            data_incasarii=luna_zi(TEST_YEAR, luna),
            fisier=pdf_justificativ(f"chitanta_{TEST_YEAR}_{luna:02d}_{i + 1}"),
            valuta="RON",
            tip_tranzactie=fake.random_element(["BANCAR", "NUMERAR"]),
            sursa_venit=SURSA_ACTIVITATE if i % 2 == 0 else SURSA_ALTELE,
        )
        ramas -= suma

    # --- Verificari DB pentru luna curenta ---------------------------------
    nr_incasari = db.execute(
        "SELECT COUNT(*) FROM incasari_incasarimodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}-{luna:02d}%",),
    ).fetchone()[0]
    assert 2 <= nr_incasari <= 5

    # Incasarile din facturi sunt legate de factura si au PDF-ul atasat.
    legate = db.execute(
        "SELECT COUNT(*) FROM incasari_incasarimodel i "
        "JOIN facturi_facturamodel f ON i.factura_id = f.id "
        "WHERE i.data_inserarii LIKE ? AND i.fisier != ''",
        (f"{TEST_YEAR}-{luna:02d}%",),
    ).fetchone()[0]
    assert legate == 2


# ---------------------------------------------------------------------------
# 3. Cheltuieli diverse + TVA taxare inversa + mijloace fixe, luna cu luna
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("luna", range(1, LAST_MONTH + 1))
def test_03_cheltuieli(page, db, luna):
    nume_uri_adaugate = []

    def _cheltuiala(**kwargs):
        adauga_cheltuiala(
            page,
            fisier=pdf_justificativ(
                f"doc_cheltuiala_{TEST_YEAR}_{luna:02d}_{len(nume_uri_adaugate) + 1:02d}"
            ),
            **kwargs,
        )
        nume_uri_adaugate.append(kwargs["nume"])

    # --- 3 cheltuieli integral deductibile (unele in EUR) ------------------
    for i in range(3):
        nume = f"{fake.random_element(CHELTUIELI_INTEGRALE)} {luna:02d}-{i + 1}"
        in_eur = i == 1
        _cheltuiala(
            nume=nume,
            suma=round(fake.random_int(20, 120), 2)
            if in_eur
            else round(fake.random_int(80, 600), 2),
            valuta="EUR" if in_eur else "RON",
            data_cheltuielii=luna_zi(TEST_YEAR, luna),
            tip_tranzactie=fake.random_element(["BANCAR", "NUMERAR"]),
        )

    # --- 1 obiect de inventar ----------------------------------------------
    nume_inventar = f"{fake.random_element(CHELTUIELI_INVENTAR)} {luna:02d}"
    _cheltuiala(
        nume=nume_inventar,
        suma=round(fake.random_int(600, 2400), 2),
        data_cheltuielii=luna_zi(TEST_YEAR, luna),
        deductibila=OBIECT_INVENTAR,
    )

    # --- 1 cheltuiala auto/utilitati, deductibila 50% ----------------------
    _cheltuiala(
        nume=f"Combustibil auto {luna:02d}",
        suma=round(fake.random_int(200, 700), 2),
        data_cheltuielii=luna_zi(TEST_YEAR, luna),
        deductibila=AUTO_UTILITATI_50,
    )

    # --- Servicii UE cu taxare inversa (D301 + D390) -----------------------
    furnizor_ue = FURNIZORI_UE[luna % len(FURNIZORI_UE)]
    zi_factura_ue = luna_zi(TEST_YEAR, luna, max_day=25)
    suma_ue = round(fake.random_int(40, 300) + 0.99, 2)
    nume_ue = f"Servicii cloud {furnizor_ue[0]} {luna:02d}"
    _cheltuiala(
        nume=nume_ue,
        suma=suma_ue,
        valuta="EUR",
        data_cheltuielii=zi_factura_ue,
        tip_achizitie=TIP_ACHIZITIE_UE,
        furnizor_denumire=furnizor_ue[0],
        furnizor_tara=furnizor_ue[1],
        furnizor_cod_fiscal=furnizor_ue[2],
        numar_factura=fake.bothify(f"{furnizor_ue[1]}-{TEST_YEAR}-######").upper(),
        data_facturii=zi_factura_ue,
    )

    # --- Servicii non-UE cu taxare inversa (doar D301) ---------------------
    furnizor_non = FURNIZORI_NON_UE[luna % len(FURNIZORI_NON_UE)]
    zi_factura_non = luna_zi(TEST_YEAR, luna, max_day=25)
    suma_non = round(fake.random_int(10, 120) + 0.99, 2)
    nume_non = f"Abonament SaaS {furnizor_non[0]} {luna:02d}"
    _cheltuiala(
        nume=nume_non,
        suma=suma_non,
        valuta="USD",
        data_cheltuielii=zi_factura_non,
        tip_achizitie=TIP_ACHIZITIE_NON_UE,
        furnizor_denumire=furnizor_non[0],
        furnizor_tara=furnizor_non[1],
        furnizor_cod_fiscal=furnizor_non[2],
        numar_factura=fake.bothify(f"INV-{TEST_YEAR}-########").upper(),
        data_facturii=zi_factura_non,
    )

    # --- Mijloc fix (2-3 pe an: lunile 1, 5, 9) -----------------------------
    for mf in MIJLOACE_FIXE:
        if _luna_mijloc_fix(mf["luna"]) != luna:
            continue
        zi_punere = luna_zi(TEST_YEAR, luna, max_day=20)
        _cheltuiala(
            nume=mf["nume"],
            suma=round(fake.random_int(*mf["suma"]), 2),
            data_cheltuielii=zi_punere,
            deductibila=MIJLOC_FIX,
            cod_de_clasificare=mf["cod"],
            ani_amortizare=mf["ani"],
            data_punerii_in_functiune=zi_punere,
        )

    # --- Verificari DB pentru luna curenta ---------------------------------
    nr_cheltuieli = db.execute(
        "SELECT COUNT(*) FROM cheltuieli_cheltuialamodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}-{luna:02d}%",),
    ).fetchone()[0]
    assert nr_cheltuieli <= 10

    # Taxarea inversa: baza in lei si TVA autolichidata (21%) calculate.
    for nume, tip in ((nume_ue, TIP_ACHIZITIE_UE), (nume_non, TIP_ACHIZITIE_NON_UE)):
        row = db.execute(
            "SELECT * FROM cheltuieli_cheltuialamodel WHERE nume_cheltuiala = ?",
            (nume,),
        ).fetchone()
        assert row is not None, f"Cheltuiala {nume!r} nu a fost salvata"
        assert row["tip_achizitie"] == tip
        assert row["curs_bnr_aplicat"] and row["curs_bnr_aplicat"] > 1
        assert row["baza_in_lei"] == pytest.approx(
            row["suma"] * row["curs_bnr_aplicat"], abs=0.02
        )
        assert row["tva_autolichidata"] == pytest.approx(
            row["baza_in_lei"] * COTA_TVA, abs=0.02
        )
        # TVA-ul autolichidat se adauga la cheltuiala deductibila.
        assert row["deducere_in_ron"] == pytest.approx(
            row["suma_in_ron"] + row["tva_autolichidata"], abs=0.02
        )

    # Obiectul de inventar e marcat ca atare; auto/utilitati dedus 50%.
    inventar = db.execute(
        "SELECT obiect_de_inventar FROM cheltuieli_cheltuialamodel "
        "WHERE nume_cheltuiala = ?",
        (nume_inventar,),
    ).fetchone()
    assert inventar["obiect_de_inventar"] == 1
    auto = db.execute(
        "SELECT suma_in_ron, deducere_in_ron FROM cheltuieli_cheltuialamodel "
        "WHERE nume_cheltuiala = ?",
        (f"Combustibil auto {luna:02d}",),
    ).fetchone()
    assert auto["deducere_in_ron"] == pytest.approx(auto["suma_in_ron"] / 2, abs=0.02)


# ---------------------------------------------------------------------------
# 4. Verificari finale pe tot anul
# ---------------------------------------------------------------------------


def test_04_venit_total_sub_plafon(page, db):
    total = db.execute(
        "SELECT COALESCE(SUM(suma_in_ron), 0) FROM incasari_incasarimodel "
        "WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]
    assert total > 0, "Nu exista incasari inregistrate"
    assert total < VENIT_MAX_RON, (
        f"Venitul total {total:.2f} RON depaseste plafonul de {VENIT_MAX_RON} RON"
    )

    # Fiecare luna are incasari (max. 5) si cheltuieli (max. 10).
    for luna in range(1, LAST_MONTH + 1):
        nr_i = db.execute(
            "SELECT COUNT(*) FROM incasari_incasarimodel WHERE data_inserarii LIKE ?",
            (f"{TEST_YEAR}-{luna:02d}%",),
        ).fetchone()[0]
        nr_c = db.execute(
            "SELECT COUNT(*) FROM cheltuieli_cheltuialamodel WHERE data_inserarii LIKE ?",
            (f"{TEST_YEAR}-{luna:02d}%",),
        ).fetchone()[0]
        assert 1 <= nr_i <= 5, f"Luna {luna}: {nr_i} incasari"
        assert 1 <= nr_c <= 10, f"Luna {luna}: {nr_c} cheltuieli"


def test_05_mijloace_fixe_si_tva_anual(page, db):
    # 2-3 mijloace fixe pe an, cu amortizare calculata.
    mijloace = db.execute(
        "SELECT * FROM cheltuieli_cheltuialamodel WHERE mijloc_fix = 1"
    ).fetchall()
    assert 2 <= len(mijloace) <= 3
    for mf in mijloace:
        assert mf["amortizare_lunara"] == pytest.approx(
            mf["suma_in_ron"] / (mf["ani_amortizare"] * 12), abs=0.02
        )
        assert mf["data_inceperii_amortizarii"]
        assert mf["data_amortizarii_complete"]
        assert mf["cod_de_clasificare"].endswith(".")

    # Ambele tipuri de taxare inversa sunt prezente (UE si non-UE).
    ue = db.execute(
        "SELECT COUNT(*), SUM(tva_autolichidata) FROM cheltuieli_cheltuialamodel "
        "WHERE tip_achizitie = ?",
        (TIP_ACHIZITIE_UE,),
    ).fetchone()
    non_ue = db.execute(
        "SELECT COUNT(*), SUM(tva_autolichidata) FROM cheltuieli_cheltuialamodel "
        "WHERE tip_achizitie = ?",
        (TIP_ACHIZITIE_NON_UE,),
    ).fetchone()
    assert ue[0] == LAST_MONTH and ue[1] > 0
    assert non_ue[0] == LAST_MONTH and non_ue[1] > 0

    # TVA-ul total de plata prin D301 pe an.
    tva_total = db.execute(
        "SELECT SUM(tva_autolichidata) FROM cheltuieli_cheltuialamodel "
        "WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]
    assert tva_total == pytest.approx(ue[1] + non_ue[1], abs=0.05)


def test_06_verificari_ui(page, db):
    """Cateva verificari directe in interfata (tabele, TVA D301, amortizare)."""
    # Un mijloc fix apare in tabel cu suma dedusa integral.
    mf = db.execute(
        "SELECT nume_cheltuiala, suma_in_ron FROM cheltuieli_cheltuialamodel "
        "WHERE mijloc_fix = 1 LIMIT 1"
    ).fetchone()
    row = rand_cheltuiala(page, mf["nume_cheltuiala"])
    expect(row).to_be_visible()
    assert cell_float(row, 5) == pytest.approx(mf["suma_in_ron"], abs=0.02)

    # O cheltuiala cu taxare inversa afiseaza TVA-ul in coloana "TVA D301".
    tva_row = db.execute(
        "SELECT nume_cheltuiala, tva_autolichidata FROM cheltuieli_cheltuialamodel "
        "WHERE tip_achizitie = ? LIMIT 1",
        (TIP_ACHIZITIE_UE,),
    ).fetchone()
    row = rand_cheltuiala(page, tva_row["nume_cheltuiala"])
    assert cell_float(row, 6) == pytest.approx(tva_row["tva_autolichidata"], abs=0.02)
    expect(row.locator("td").nth(6)).to_contain_text("🇪🇺")

    # Facturile emise au PDF generat si descarcat din tabel.
    page.goto("/facturi/")
    primul_rand = page.locator("#tabel-facturi tbody tr").first
    expect(primul_rand.locator("a[href*='.pdf']").first).to_be_visible()

    # Pagina Registre se incarca pentru anul testat.
    page.goto("/registre/")
    expect(page.locator("h1").first).to_be_visible()


def test_07_declaratii_tva_din_cheltuieli(page, db):
    """Filtrul 'Cheltuieli externe (TVA)' pe luna + butonul Descarca:
    zip cu D301/D390 (UE) si D301 (non-UE), jurnal si instructiuni de plata."""
    luna = LAST_MONTH
    page.goto(f"/cheltuieli/?extern=1&anul_extern={TEST_YEAR}&luna_extern={luna}")

    filtru = page.locator("#filtru-extern")
    expect(filtru).to_have_value(str(luna))

    # In luna filtrata apar doar facturile UE/non-UE (2 in scenariu).
    randuri = page.locator("#tabel-cheltuieli tbody tr")
    assert randuri.count() == 2

    with page.expect_download() as download_info:
        page.locator("#filtru-tva").get_by_role("button", name="Descarca").click()
    download = download_info.value
    assert download.suggested_filename == f"D301-D390_{TEST_YEAR}_{luna:02d}.zip"

    import io
    import tempfile
    from zipfile import ZipFile

    import pandas as pd

    zip_path = Path(tempfile.mkdtemp()) / download.suggested_filename
    download.save_as(zip_path)
    with ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Cate un folder pe cod: UE pe codul special art. 317, non-UE pe CIF.
        foldere = {n.split("/")[0] for n in names}
        assert len(foldere) == 2
        for cod in foldere:
            assert f"{cod}/D301_{TEST_YEAR}_{luna:02d}.md" in names
            assert f"{cod}/Jurnal_cumparari_{TEST_YEAR}_{luna:02d}.xlsx" in names
            df = pd.read_excel(io.BytesIO(zf.read(f"{cod}/Jurnal_cumparari_{TEST_YEAR}_{luna:02d}.xlsx")))
            # Jurnalul fiecarui folder contine doar factura declarata pe codul lui.
            assert len(df) == 1
            assert (df["Referinta cod"] == "15-16").all()
        # D390 doar in folderul codului intracomunitar (UE).
        d390_names = [n for n in names if "D390_" in n]
        assert len(d390_names) == 1
        assert d390_names[0].endswith(".md")
        # Fara XML-uri in zip.
        assert not any(n.endswith(".xml") for n in names)

    # Jurnalul de cumparari din Registre contine facturile cu taxare inversa.
    nr_taxare = db.execute(
        "SELECT COUNT(*) FROM cheltuieli_cheltuialamodel WHERE tip_achizitie IN (?, ?)",
        (TIP_ACHIZITIE_UE, TIP_ACHIZITIE_NON_UE),
    ).fetchone()[0]
    page.goto(f"/registre/?anul={TEST_YEAR}")
    page.get_by_role("button", name="Jurnal Cumparaturi").click()
    jurnal_randuri = page.locator("div[x-show=\"active == 'jurnale'\"] tbody tr")
    expect(jurnal_randuri.first).to_be_visible()
    assert jurnal_randuri.count() == nr_taxare  # fara rand de total
