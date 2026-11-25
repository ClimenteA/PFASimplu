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
src/tests/.runtime/test.db pentru inspectie ulterioara.
"""

import datetime
from pathlib import Path

import pytest
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
    assert_saved,
    cell_float,
    completare_setari,
    emite_factura,
    incasare_din_factura,
    incasare_separata,
    pdf_justificativ,
    rand_cheltuiala,
)
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

# Valorile calculate (suma in RON, deducere, TVA, amortizare) sunt
# proprietati pe modele, nu coloane; le verificam prin ORM, pe aceeasi baza
# de date cu serverul de test ( PFASIMPLU_DB_PATH setat in conftest ).
import django

django.setup()

from cheltuieli.calcul import q_inventar, q_mijloc_fix, q_scos_din_uz
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from utils.tari import TARI_NON_UE_CHOICES, TARI_UE_CHOICES

UE_CODES = [cod for cod, _ in TARI_UE_CHOICES]
NON_UE_CODES = [cod for cod, _ in TARI_NON_UE_CHOICES]

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
        # Numele contine "/" ca sa acopere exportul Registrului-inventar:
        # felul documentului ajunge in numele unui zip si trebuie sanitizat.
        "nume": "Laptop Dell Latitude 7450 / docking station",
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
    total_luna_ron = float(
        sum(
            (
                i.suma_in_ron
                for i in IncasariModel.objects.filter(
                    data_incasarii__year=TEST_YEAR, data_incasarii__month=luna
                )
            ),
            0,
        )
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
        c = CheltuialaModel.objects.get(nume_cheltuiala=nume)
        assert c.tip_achizitie == tip
        assert c.curs_bnr_aplicat and c.curs_bnr_aplicat > 1
        assert float(c.baza_in_lei) == pytest.approx(
            float(c.suma) * float(c.curs_bnr_aplicat), abs=0.02
        )
        assert float(c.tva_autolichidata) == pytest.approx(
            float(c.baza_in_lei) * COTA_TVA, abs=0.02
        )
        # TVA-ul autolichidat se adauga la cheltuiala deductibila.
        assert float(c.deducere_in_ron) == pytest.approx(
            float(c.suma_in_ron) + float(c.tva_autolichidata), abs=0.02
        )

    # Obiectul de inventar e marcat ca atare; auto/utilitati dedus 50%.
    assert CheltuialaModel.objects.get(nume_cheltuiala=nume_inventar).obiect_de_inventar
    auto = CheltuialaModel.objects.get(nume_cheltuiala=f"Combustibil auto {luna:02d}")
    assert float(auto.deducere_in_ron) == pytest.approx(
        float(auto.suma_in_ron) / 2, abs=0.02
    )


# ---------------------------------------------------------------------------
# 4. Verificari finale pe tot anul
# ---------------------------------------------------------------------------


def test_04_venit_total_sub_plafon(page, db):
    total = IncasariModel.get_total_incasari(TEST_YEAR)
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
    mijloace = list(CheltuialaModel.objects.filter(q_mijloc_fix()))
    assert 2 <= len(mijloace) <= 3
    for mf in mijloace:
        assert float(mf.amortizare_lunara) == pytest.approx(
            float(mf.suma_in_ron) / (mf.ani_amortizare * 12), abs=0.02
        )
        assert mf.data_inceperii_amortizarii
        assert mf.data_amortizarii_complete
        assert mf.cod_de_clasificare.endswith(".")

    # Ambele tipuri de taxare inversa sunt prezente (UE si non-UE).
    ue = list(CheltuialaModel.objects.filter(furnizor_tara__in=UE_CODES))
    non_ue = list(CheltuialaModel.objects.filter(furnizor_tara__in=NON_UE_CODES))
    tva_ue = sum((c.tva_autolichidata for c in ue), 0)
    tva_non_ue = sum((c.tva_autolichidata for c in non_ue), 0)
    assert len(ue) == LAST_MONTH and tva_ue > 0
    assert len(non_ue) == LAST_MONTH and tva_non_ue > 0

    # TVA-ul total de plata prin D301 pe an.
    tva_total = sum(
        (
            c.tva_autolichidata
            for c in CheltuialaModel.objects.filter(data_inserarii__year=TEST_YEAR)
            if c.tva_autolichidata
        ),
        0,
    )
    assert float(tva_total) == pytest.approx(
        float(tva_ue) + float(tva_non_ue), abs=0.05
    )


def test_06_verificari_ui(page, db):
    """Cateva verificari directe in interfata (tabele, TVA D301, amortizare)."""
    # Un mijloc fix apare in tabel cu suma dedusa integral.
    mf = CheltuialaModel.objects.filter(q_mijloc_fix()).first()
    row = rand_cheltuiala(page, mf.nume_cheltuiala)
    expect(row).to_be_visible()
    assert cell_float(row, 5) == pytest.approx(float(mf.suma_in_ron), abs=0.02)

    # O cheltuiala cu taxare inversa afiseaza TVA-ul in coloana "TVA D301".
    tva_row = CheltuialaModel.objects.filter(furnizor_tara__in=UE_CODES).first()
    row = rand_cheltuiala(page, tva_row.nume_cheltuiala)
    assert cell_float(row, 6) == pytest.approx(
        float(tva_row.tva_autolichidata), abs=0.02
    )
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
        # Cate un folder pe cod, cu prefix: TVA (cod intracomunitar) si CIF (cod normal).
        foldere = {n.split("/")[0] for n in names}
        assert len(foldere) == 2
        assert any(f.startswith("TVA-") for f in foldere)
        assert any(f.startswith("CIF-") for f in foldere)
        for cod in foldere:
            assert f"{cod}/D301_{TEST_YEAR}_{luna:02d}.md" in names
            assert f"{cod}/Jurnal_cumparari_{TEST_YEAR}_{luna:02d}.xlsx" in names
            # Factura furnizorului atasata cheltuielii, inclusa per cod.
            assert any(n.startswith(f"{cod}/facturi/") for n in names)
            df = pd.read_excel(
                io.BytesIO(
                    zf.read(f"{cod}/Jurnal_cumparari_{TEST_YEAR}_{luna:02d}.xlsx")
                )
            )
            # Jurnalul fiecarui folder contine doar factura declarata pe codul lui.
            assert len(df) == 1
            assert (df["Referinta cod"] == "15-16").all()
        # D390 doar in folderul TVA (UE).
        d390_names = [n for n in names if "D390_" in n]
        assert len(d390_names) == 1
        assert d390_names[0].startswith("TVA-") and d390_names[0].endswith(".md")
        # Fara XML-uri in zip.
        assert not any(n.endswith(".xml") for n in names)

    # Jurnalul de cumparari din Registre contine facturile cu taxare inversa.
    nr_taxare = CheltuialaModel.objects.filter(
        furnizor_tara__in=UE_CODES + NON_UE_CODES
    ).count()
    page.goto(f"/registre/?anul={TEST_YEAR}")
    page.get_by_role("button", name="Jurnal Cumparaturi").click()
    jurnal_randuri = page.locator("div[x-show=\"active == 'jurnale'\"] tbody tr")
    expect(jurnal_randuri.first).to_be_visible()
    assert jurnal_randuri.count() == nr_taxare  # fara rand de total


def test_08_export_date_pe_an(page, db):
    """Exportul din Setari pe anul selectat: zip cu documente/, cheltuieli/,
    incasari/, registrele xlsx, fisele mijloacelor fixe si SUMAR.html."""
    import io
    import tempfile
    from zipfile import ZipFile

    import pandas as pd

    # Un document urcat in pagina Documente pentru anul testat.
    page.goto("/documente/")
    page.select_option("#id_tip_document", "UTIL")
    page.fill("#id_document_pentru_anul", f"{TEST_YEAR}-06-15")
    page.fill("#id_mentiuni", "Document pentru testul de export")
    page.set_input_files("#id_fisier", pdf_justificativ("document_export"))
    page.get_by_role("button", name="Adauga document").click()
    assert_saved(page)

    nr_incasari = db.execute(
        "SELECT COUNT(*) FROM incasari_incasarimodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]
    nr_cheltuieli = db.execute(
        "SELECT COUNT(*) FROM cheltuieli_cheltuialamodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]
    nr_mijloace_fixe = (
        CheltuialaModel.objects.filter(q_mijloc_fix()).exclude(q_scos_din_uz()).count()
    )

    page.goto("/setari/")
    expect(page.locator("#anul-export")).to_have_value(str(TEST_YEAR))

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Exporta datele din aplicatie").click()
    download = download_info.value
    assert download.suggested_filename == f"export_date_{TEST_YEAR}.zip"

    zip_path = Path(tempfile.mkdtemp()) / download.suggested_filename
    download.save_as(zip_path)
    with ZipFile(zip_path) as zf:
        names = zf.namelist()

        # Documentele justificative, grupate pe foldere.
        assert sum(n.startswith("documente/") for n in names) >= 1
        assert sum(n.startswith("cheltuieli/") for n in names) == nr_cheltuieli
        assert sum(n.startswith("incasari/") for n in names) >= nr_incasari

        # Registrele anului, in format xlsx, in root.
        for registru in ("Registru_Jurnal", "Registru_Fiscal", "Registru_Inventar"):
            assert f"{registru}_{TEST_YEAR}.xlsx" in names
        assert f"Jurnal_Cumparaturi_{TEST_YEAR}.xlsx" in names

        df_jurnal = pd.read_excel(
            io.BytesIO(zf.read(f"Registru_Jurnal_{TEST_YEAR}.xlsx"))
        )
        assert "Incasari Banca" in df_jurnal.columns
        assert "Plati Banca" in df_jurnal.columns

        df_cumparari = pd.read_excel(
            io.BytesIO(zf.read(f"Jurnal_Cumparaturi_{TEST_YEAR}.xlsx"))
        )
        nr_taxare = CheltuialaModel.objects.filter(
            furnizor_tara__in=UE_CODES + NON_UE_CODES
        ).count()
        assert len(df_cumparari) == nr_taxare

        # Coloana cu numele fisierului justificativ, per rand; fisierele
        # listate se regasesc in folderul cheltuieli/ din zip.
        assert "Document justificativ (fisier)" in df_cumparari.columns
        fisiere_justificative = df_cumparari["Document justificativ (fisier)"].tolist()
        assert all(fisiere_justificative)
        for nume_fisier in fisiere_justificative:
            assert f"cheltuieli/{nume_fisier}" in names

        # Fisele mijloacelor fixe (PDF), cate una per mijloc fix activ.
        fise = [n for n in names if n.startswith("fise_mijloace_fixe/")]
        assert len(fise) == nr_mijloace_fixe
        assert all(n.endswith(".pdf") for n in fise)

        # SUMAR.html cu metricile anului (pagina standalone, stil PicoCSS inline).
        assert "SUMAR.html" in names
        sumar = zf.read("SUMAR.html").decode("utf-8")
        assert f"SUMAR {TEST_YEAR}" in sumar
        assert "cdn.jsdelivr.net/npm/@picocss/pico@2" in sumar  # PicoCSS de pe CDN
        assert "Total incasari (brut)" in sumar
        assert "Total taxe si impozite estimate" in sumar
        assert "Numar incasari inregistrate" in sumar and str(nr_incasari) in sumar
        assert "Numar cheltuieli inregistrate" in sumar and str(nr_cheltuieli) in sumar
        ultima_factura = db.execute(
            "SELECT serie, numar FROM facturi_facturamodel "
            "ORDER BY data_emitere DESC, id DESC LIMIT 1"
        ).fetchone()
        assert ultima_factura  # scenariul emite facturi in fiecare luna
        assert "Ultima factura emisa" in sumar
        assert f"<td>{ultima_factura[0]}</td>" in sumar
        assert f"<td>{ultima_factura[1]}</td>" in sumar
        assert "Cea mai mare incasare" in sumar
        assert "Cea mai mare cheltuiala" in sumar
        assert "Venit net mediu pe luna (dupa taxe)" in sumar
        assert "Taxe si impozite medii pe luna" in sumar

        # Tabel de amortizare per mijloc fix (An, Luna, Suma), pana la
        # amortizarea completa (mijloacele din scenariu se amortizeaza 3-10 ani).
        assert "Amortizari mijloace fixe" in sumar
        assert "Tabel Amortizare" in sumar
        assert "Suma (RON)" in sumar
        nr_mf_active = (
            CheltuialaModel.objects.filter(q_mijloc_fix())
            .exclude(q_scos_din_uz())
            .count()
        )
        assert sumar.count("Tabel Amortizare") == nr_mf_active


def _salveaza_descarcarea(page, link, filename: str):
    """Apasa un link de descarcare si salveaza fisierul rezultat."""
    import tempfile

    with page.expect_download() as download_info:
        link.click()
    download = download_info.value
    assert download.suggested_filename == filename
    file_path = Path(tempfile.mkdtemp()) / download.suggested_filename
    download.save_as(file_path)
    return file_path


def _descarca_din_registru(page, tab_selector: str, filetype: str, filename: str):
    """Apasa iconita CSV/XLSX dintr-un tab al paginii Registre si salveaza
    fisierul descarcat (CSV sau XLSX), fara arhiva zip."""
    tab = page.locator(tab_selector)
    expect(tab).to_be_visible()
    return _salveaza_descarcarea(
        page, tab.locator(f"a[href*='filetype={filetype}'] i"), filename
    )


def test_09_descarcare_registru_jurnal(page, db):
    """Iconitele CSV si XLSX din tabul 'Registru jurnal' descarca direct un
    singur fisier cu registrul (antet si totaluri lunare), fara documente."""
    import pandas as pd

    nr_incasari = db.execute(
        "SELECT COUNT(*) FROM incasari_incasarimodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]
    nr_cheltuieli = db.execute(
        "SELECT COUNT(*) FROM cheltuieli_cheltuialamodel WHERE data_inserarii LIKE ?",
        (f"{TEST_YEAR}%",),
    ).fetchone()[0]

    page.goto(f"/registre/?anul={TEST_YEAR}")
    page.get_by_role("button", name="Registru jurnal").click()

    for filetype, extensie in (("CSV", "csv"), ("XLSX", "xlsx")):
        nume_registru = f"registru_jurnal_incasari_si_plati.{extensie}"
        file_path = _descarca_din_registru(
            page,
            "div[x-show=\"active == 'rjip'\"]",
            filetype,
            nume_registru,
        )

        if extensie == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        for coloana in (
            "Nr.Crt.",
            "Data",
            "Documentul (fel, numar)",
            "Felul operatiunii (explicatii)",
            "Incasari Numerar",
            "Incasari Banca",
            "Plati Numerar",
            "Plati Banca",
        ):
            assert coloana in df.columns
        assert len(df) >= nr_incasari + nr_cheltuieli  # + randurile de total lunar
        explicatii = df["Felul operatiunii (explicatii)"].astype(str)
        assert explicatii.str.contains("Incasare").any()
        assert explicatii.str.contains("Cheltuiala").any()
        assert explicatii.str.contains("Calcul total luna").any()


def test_10_descarcare_registru_inventar(page, db):
    """Iconitele CSV si XLSX din tabul 'Registru inventar' descarca direct un
    singur fisier cu registrul, fara documente sau fisele mijloacelor fixe."""
    import pandas as pd

    nr_inventar = (
        CheltuialaModel.objects.filter(q_inventar()).exclude(q_scos_din_uz()).count()
    )
    assert nr_inventar > 0

    page.goto(f"/registre/?anul={TEST_YEAR}")
    page.get_by_role("button", name="Registru inventar").click()

    for filetype, extensie in (("CSV", "csv"), ("XLSX", "xlsx")):
        nume_registru = f"registru_inventar.{extensie}"
        file_path = _descarca_din_registru(
            page,
            "div[x-show=\"active == 'rinv'\"]",
            filetype,
            nume_registru,
        )

        if extensie == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        for coloana in (
            "Nr.Crt.",
            "Denumirea elementelor inventariate",
            "Valoare inventar",
            "Data",
            "Document",
        ):
            assert coloana in df.columns
        assert len(df) == nr_inventar
        denumiri = df["Denumirea elementelor inventariate"].astype(str)
        assert denumiri.str.contains("/").any()  # numele cu slash din scenariu


def test_11_export_fara_document_justificativ(page, db):
    """Un document justificativ sters/mutat de pe disc nu trebuie sa blocheze
    descarcarea registrelor; exportul nici nu mai citeste documentele, ci
    scrie direct fisierul CSV/XLSX."""
    import uuid

    import pandas as pd

    incasare = db.execute(
        "SELECT id, fisier FROM incasari_incasarimodel "
        "WHERE data_inserarii LIKE ? LIMIT 1",
        (f"{TEST_YEAR}%",),
    ).fetchone()
    mf_obj = CheltuialaModel.objects.filter(q_mijloc_fix()).first()
    mijloc_fix = {"id": mf_obj.id, "fisier": mf_obj.fisier.name} if mf_obj else None
    assert incasare and mijloc_fix

    fisier_lipsa = f"{uuid.uuid4().hex[:8]}_document_lipsa.pdf"
    try:
        for tabel, rand in (
            ("incasari_incasarimodel", incasare),
            ("cheltuieli_cheltuialamodel", mijloc_fix),
        ):
            db.execute(
                f"UPDATE {tabel} SET fisier = ? WHERE id = ?",
                (fisier_lipsa, rand["id"]),
            )
        db.commit()

        page.goto(f"/registre/?anul={TEST_YEAR}")
        page.get_by_role("button", name="Registru jurnal").click()
        csv_path = _descarca_din_registru(
            page,
            "div[x-show=\"active == 'rjip'\"]",
            "CSV",
            "registru_jurnal_incasari_si_plati.csv",
        )
        assert len(pd.read_csv(csv_path)) > 0

        page.get_by_role("button", name="Registru inventar").click()
        xlsx_path = _descarca_din_registru(
            page,
            "div[x-show=\"active == 'rinv'\"]",
            "XLSX",
            "registru_inventar.xlsx",
        )
        assert len(pd.read_excel(xlsx_path)) > 0
    finally:
        for tabel, rand in (
            ("incasari_incasarimodel", incasare),
            ("cheltuieli_cheltuialamodel", mijloc_fix),
        ):
            db.execute(
                f"UPDATE {tabel} SET fisier = ? WHERE id = ?",
                (rand["fisier"], rand["id"]),
            )
        db.commit()


def test_12_descarcare_liste_fara_zip(page, db):
    """Iconitele CSV/XLSX din Facturi, Incasari si Cheltuieli descarca un
    singur fisier cu toate inregistrarile, fara zip si fara paginare."""
    import pandas as pd

    for page_path, tabel, nume_fisier in (
        ("/facturi/", "facturi_facturamodel", "facturi"),
        ("/incasari/", "incasari_incasarimodel", "incasari"),
        ("/cheltuieli/", "cheltuieli_cheltuialamodel", "cheltuieli"),
    ):
        nr_inregistrari = db.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
        assert nr_inregistrari > 0

        page.goto(page_path)
        for filetype, extensie in (("CSV", "csv"), ("XLSX", "xlsx")):
            file_path = _salveaza_descarcarea(
                page,
                page.locator(f"a[href*='filetype={filetype}'] i").first,
                f"{nume_fisier}.{extensie}",
            )

            if extensie == "csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            assert len(df) == nr_inregistrari
