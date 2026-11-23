"""Generarea documentelor TVA pentru declaratiile D301/D390.

Declaratiile se genereaza ca fisiere Markdown completate (antetul declaratiei,
sectiunile cu toate valorile, termene si instructiuni de plata), dupa modelul
ghidurilor din stocare/completare-declaratii-tva.

Zip-ul este grupat pe codul de identificare fiscala: cate un folder pentru
fiecare CIF / cod TVA intracomunitar pe care se depun declaratii (UE pe codul
special art. 317, non-UE pe CIF-ul normal), fiecare cu D301 (si D390 pentru UE)
si jurnalul de cumparari in Excel cu facturile declarate pe codul respectiv.
"""

import os
import re
from zipfile import ZipFile

import pandas as pd
from fpdf_table import PDFTable, Align

from core.settings import get_extracts_path, get_font_path
from setari.models import SetariModel
from utils.pretty_excel import make_excel_pretty
from utils.trezorerie import COD_BUGETAR_TVA, get_link_iban_trezorerie
from utils.tva import (
    COD_REFERINTA_JURNAL,
    DENUMIRE_REFERINTA_JURNAL,
    calculeaza_d301_lista,
    calculeaza_d390,
    calculeaza_jurnal_cumparari,
    get_cheltuieli_taxare_inversa,
    round2,
)


LUNI_RO = {
    1: "ianuarie", 2: "februarie", 3: "martie", 4: "aprilie",
    5: "mai", 6: "iunie", 7: "iulie", 8: "august",
    9: "septembrie", 10: "octombrie", 11: "noiembrie", 12: "decembrie",
}


def _fmt_num(value) -> str:
    """Numere fara zecimale inutile: 21.0 -> '21', 112.24 -> '112.24'."""
    if value is None:
        return "0"
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text or "0"


def _md_num(value) -> str:
    """Numere in format romanesc pentru tabelele Markdown: 112.24 -> '112,24'."""
    return _fmt_num(value).replace(".", ",")


def _denumire_pfa(setari: SetariModel) -> str:
    nume = (setari.nume or "").strip()
    if "PERSOANA FIZICA AUTORIZATA" in nume.upper() or nume.upper().endswith("PFA"):
        return nume
    return f"{nume} PERSOANA FIZICA AUTORIZATA"


def _adresa_declarant(setari: SetariModel) -> str:
    localitate = (setari.localitate or "").split(",")[-1].strip()
    return f"{localitate} {setari.adresa}".strip()


def _este_cod_special(setari: SetariModel, cif: str) -> bool:
    cod_special = (setari.cod_tva_intracomunitar or "").strip().upper().removeprefix("RO")
    return bool(cod_special) and cif == cod_special


# ---------------------------------------------------------------------------
# Declaratiile completate, in Markdown
# ---------------------------------------------------------------------------

D301_HEADER_SECTIUNE = (
    "| Nr. crt. | Document Număr/Data | Valoare în valută | Tip valută | Curs de schimb | Baza de impozitare (lei) | TVA datorat (lei) |\n"
    "|---:|---|---:|---|---:|---:|---:|"
)


def _d301_rand_md(r: dict) -> str:
    return (
        f'| {r["nr_crt"]} | `{r["nr_doc"]}` / `{r["data_doc"]}` '
        f'| {_md_num(r["val_valuta"])} | `{r["tip_valuta"]}` '
        f'| {_md_num(r["curs_valutar"])} | {_md_num(r["baza"])} | {_md_num(r["tva"])} |'
    )


def genereaza_d301_md(d301: dict, setari: SetariModel) -> str:
    """D301 completat in Markdown: date de identificare, sectiunile 4 si 4.1,
    termen, suma de plata si instructiunea de plata la trezorerie."""
    cod_special = _este_cod_special(setari, d301["cif"])
    if cod_special:
        tip_cod = "cod special de TVA intracomunitar (art. 317)"
        calitate = "bifat **„Persoane care sunt înregistrate conform art. 317 din Legea nr. 227/2015”**"
    else:
        tip_cod = "codul normal de PFA (CIF) - achiziții de servicii din afara UE"
        calitate = "persoană fizică autorizată (CIF normal), pentru achizițiile de servicii din afara UE"

    linii = [
        f'# D301 - Decont special de TVA - {LUNI_RO[d301["luna"]]} {d301["anul"]}',
        "",
        f'**Perioada de raportare:** luna {d301["luna"]:02d} / anul {d301["anul"]}  ',
        f'**Cod de identificare fiscală:** `RO{d301["cif"]}` - {tip_cod}  ',
        f'**Denumire:** {_denumire_pfa(setari)}  ',
        f'**Domiciliul fiscal:** {_adresa_declarant(setari)}',
        "",
        "> **Atenție la codul folosit:** achizițiile din UE se declară pe **codul special de TVA",
        "> intracomunitar** din Setări, iar cele din afara UE pe **CIF-ul normal** al PFA-ului.",
        "> Nu înlocuiți un cod cu altul.",
        "",
        "## 1. Date de identificare",
        "",
        "| Câmp | Valoare |",
        "|---|---|",
        f'| Cod de identificare fiscală | `{d301["cif"]}` - {tip_cod} |',
        "| Prefix | `RO` (bifat) |",
        f"| Denumire / Nume, Prenume | `{_denumire_pfa(setari)}` |",
        f"| Domiciliul fiscal | `{_adresa_declarant(setari)}` |",
        f'| Cont | `{setari.get_iban_pentru_valuta("RON") or "-"}` |',
        f"| Calitate | {calitate} |",
        "| Declarație rectificativă | nu se bifează |",
        f'| Luna / Anul | `{d301["luna"]:02d}` / `{d301["anul"]}` |',
        "",
        "## 2. Secțiunile 1, 2 și 3",
        "",
        "Rămân **zero** - fără achiziții intracomunitare de bunuri, mijloace de transport noi sau produse accizabile.",
        "",
        "## 3. Secțiunea 4 - Operațiuni prevăzute la art. 307 alin. (2), (3), (5) și (6)",
        "",
        D301_HEADER_SECTIUNE,
    ]

    randuri4 = [r for r in d301["randuri"] if r["tip_operatie"] == "4"]
    for r in randuri4:
        linii.append(_d301_rand_md(r))
    if not randuri4:
        linii.append("| - | - | 0 | - | - | 0,00 | 0,00 |")
    linii.append(
        f'| **TOTAL** | | | | | **{_md_num(d301["baza4"])}** | **{_md_num(d301["tva4"])}** |'
    )

    linii += [
        "",
        "## 4. Secțiunea 4.1 - Achiziții de servicii intracomunitare (art. 307 alin. (2))",
        "",
    ]
    randuri5 = [r for r in d301["randuri"] if r["tip_operatie"] == "5"]
    if randuri5:
        linii.append(D301_HEADER_SECTIUNE)
        for r in randuri5:
            linii.append(_d301_rand_md(r))
        linii.append(
            f'| **TOTAL** | | | | | **{_md_num(d301["baza5"])}** | **{_md_num(d301["tva5"])}** |'
        )
        linii += [
            "",
            "> **Regulă:** factura din UE se trece **și în secțiunea 4, și în secțiunea 4.1**.",
            "> Formularul are mențiunea expresă: „Facturile declarate în Secțiunea 4.1 trebuiesc declarate și în Secțiunea 4!”.",
        ]
    else:
        linii += [
            "**Zero** - nu există achiziții de servicii din UE în această declarație",
            "(facturile din afara UE se trec doar în secțiunea 4).",
        ]

    linii += [
        "",
        "## 5. Termen și plată",
        "",
        f'- Termen depunere: **{d301["termen"].strftime("%d.%m.%Y")}** (25 inclusiv a lunii următoare exigibilității).',
        f'- TVA de plată rezultat din D301: **{_md_num(d301["total_de_plata"])} lei**.',
        "- „Suma de control” și „Nr. de evidență a plății” se generează automat de aplicația oficială ANAF; nu se inventează.",
        "",
        "### Instrucțiune de plată",
        "",
        "| Element | Valoare |",
        "|---|---|",
        "| Beneficiar | Trezoreria Statului (trezoreria operativă de domiciliul fiscal) |",
        f'| IBAN beneficiar | `{setari.cont_iban_trezoreria or "NECOMPLETAT - vezi Setari"}` |',
        f"| Cod bugetar | `{COD_BUGETAR_TVA}` - TVA încasată pentru operațiuni interne |",
        f'| Cod identificare fiscală plătitor | `{d301["cif"]}` |',
        f'| Sumă | `{_md_num(d301["total_de_plata"])} lei` |',
        f'| Explicație plată | `TVA D301 {LUNI_RO[d301["luna"]]} {d301["anul"]}` |',
        "",
        "**NU se plătește în contul unic.** TVA din D301 se plătește în contul `20A100101` al trezoreriei.",
        f"Lista IBAN-uri ANAF: {get_link_iban_trezorerie(setari.localitate)}",
        "",
        "## 6. Cum se depune",
        "",
        "**Înainte de toate:** trebuie să ai un **cont SPV (Spațiul Privat Virtual) înregistrat pe codul",
        "de TVA intracomunitar** (art. 317). Logarea pentru depunere și pentru preluarea recipiselor",
        "se face pe acel cont.",
        "",
        "1. Intră pe [e-guvernare.ro](https://www.e-guvernare.ro/) și click pe **DEPUNERE DECLARATII ANAF** (butonul redirecționează către [decl.anaf.mfinante.gov.ro](https://decl.anaf.mfinante.gov.ro/my.policy)).",
        "2. **Authentificare cu certificat** - este necesar un certificat digital calificat (de la certDigital, DigiSign, Trans Sped etc.).",
        "3. Urci PDF-ul inteligent semnat și validat.",
        "4. Te loghezi în SPV-ul pe codul TVA și descarci recipisa (dovada de încărcare declarație).",
        "5. Verifici recipisa dacă a fost încărcată fără erori.",
        "6. Plătești TVA-ul conform instrucțiunii de mai sus, până la termen.",
        "",
        "---",
        "",
        "_Temei legal: art. 307 alin. (2), art. 317, art. 324 Cod fiscal; cota 21% - art. 291 alin. (1);",
        "curs BNR din data exigibilității - art. 290 alin. (2). Generat automat de PFASimplu._",
    ]
    return "\n".join(linii)


def genereaza_d390_md(d390: dict, setari: SetariModel) -> str:
    """D390 VIES completat in Markdown: date de identificare, rezumat,
    lista operatorilor intracomunitari (tip S) si termen."""
    linii = [
        f'# D390 VIES - Declarație recapitulativă - {LUNI_RO[d390["luna"]]} {d390["anul"]}',
        "",
        f'**Perioada de raportare:** luna {d390["luna"]:02d} / anul {d390["anul"]}  ',
        f'**Cod de identificare fiscală:** `RO{d390["cif"]}` - cod special de TVA intracomunitar (art. 317)  ',
        f'**Denumire:** {_denumire_pfa(setari)}  ',
        f'**Domiciliul fiscal:** {_adresa_declarant(setari)}',
        "",
        "## 1. Date de identificare",
        "",
        "| Câmp | Valoare |",
        "|---|---|",
        f'| Anul / Luna | `{d390["anul"]}` / `{d390["luna"]:02d}` |',
        f'| Cod de identificare fiscală | `RO{d390["cif"]}` |',
        f"| Denumire / Nume, Prenume | `{_denumire_pfa(setari)}` |",
        f"| Domiciliul fiscal | `{_adresa_declarant(setari)}` |",
        f'| Număr total operatori intracomunitari | `{d390["nr_operatori"]}` |',
        "| Declarație rectificativă | nu se bifează |",
        "",
        "## 2. Rezumatul declarației",
        "",
        "| Tip operațiune | Valoare (lei) |",
        "|---|---:|",
        "| L - Livrări intracomunitare de bunuri | `0` |",
        "| T - Livrări în cadrul unei operațiuni triunghiulare | `0` |",
        "| A - Achiziții intracomunitare de bunuri | `0` |",
        "| P - Prestări intracomunitare de servicii | `0` |",
        f'| **S - Achiziții intracomunitare de servicii** | **`{d390["bazaS"]}`** |',
        "| R - Livrări în regimul special pentru agricultori | `0` |",
        "",
        "## 3. Lista operațiunilor intracomunitare",
        "",
        "| Nr. crt. | Tip | Țara | Cod operator intracomunitar | Denumire operator intracomunitar | Baza impozabilă (lei) |",
        "|---:|---|---|---|---|---:|",
    ]
    for r in d390["randuri"]:
        linii.append(
            f'| {r["nr_crt"]} | `{r["tip"]}` | `{r["tara_denumire"]}-{r["tara"]}` '
            f'| `{r["cod_operator"]}` | `{r["denumire_operator"]}` | `{r["baza"]}` |'
        )
    linii += [
        f'| **TOTAL GENERAL** | | | | | **`{d390["total_baza"]}`** |',
        "",
        "> **Codul operatorului se scrie fără prefixul de țară** (țara este coloană separată):",
        "> `ATU77164426` → țara `Austria-AT`, cod `U77164426`. Nu dublați prefixul de țară.",
        "> Baza se rotunjește la întreg în lei.",
        "",
        "## 4. Termen",
        "",
        f'- Termen depunere: **{d390["termen"].strftime("%d.%m.%Y")}** (25 inclusiv a lunii următoare).',
        "- D390 este informativă, fără plată. Se depune doar pentru operațiuni intracomunitare (UE);",
        "  pentru furnizori din afara UE nu se depune D390.",
        "",
        "---",
        "",
        "_Temei legal: art. 325 alin. (1) lit. e) Cod fiscal; instrucțiuni D390 - Ordinul nr. 705/2020.",
        "Generat automat de PFASimplu._",
    ]
    return "\n".join(linii)


# ---------------------------------------------------------------------------
# Jurnalul de cumparari (registru contabil) - PDF pentru pagina Registre
# ---------------------------------------------------------------------------

def _pdf_nou() -> PDFTable:
    pdf = PDFTable()
    pdf.add_fonts_custom(
        font_name="arial",
        font_extension="ttf",
        font_dir=get_font_path(),
        set_default=True,
    )
    return pdf


def genereaza_jurnal_cumparari_pdf(jurnal: dict, setari: SetariModel, output_path: str):
    pdf = _pdf_nou()
    perioada = (
        f'{LUNI_RO[jurnal["luna"]]} {jurnal["anul"]}'
        if jurnal["luna"]
        else f'anul {jurnal["anul"]}'
    )
    pdf.table_header(["JURNAL PENTRU CUMPARARI"], align=Align.L)
    pdf.table_row([f"{_denumire_pfa(setari)}"], option="responsive")
    pdf.table_row([f"Perioada: {perioada}"])
    pdf.table_row([""])

    width_cols = pdf.table_cols(0.5, 1.2, 1.9, 2.2, 1.7, 1.3, 1.2, 1.1, 0.8)
    pdf.table_header(
        ["Nr.", "Data", "Numar document", "Furnizor", "Cod fiscal", "Total doc. (cu TVA)", "Baza impozitare", "Valoare TVA", "Ref. cod"],
        width_cols,
        align=Align.C,
    )
    for r in jurnal["randuri"]:
        pdf.table_row(
            [
                str(r["nr_crt"]),
                r["data_doc"],
                r["nr_doc"],
                r["furnizor_denumire"],
                r["furnizor_cod_fiscal"],
                f'{r["total_document"]:.2f}',
                f'{r["baza"]:.2f}',
                f'{r["tva"]:.2f}',
                r["cod_referinta"],
            ],
            width_cols,
            option="responsive",
        )
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)
    pdf.table_row(
        ["", "", "", "", "Total", f'{jurnal["total_document"]:.2f}', f'{jurnal["total_baza"]:.2f}', f'{jurnal["total_tva"]:.2f}', ""],
        width_cols,
    )
    pdf.set_font(pdf.font, "", pdf.text_normal_size)
    pdf.table_row([""])
    pdf.table_row([f'Referinta {COD_REFERINTA_JURNAL}: {DENUMIRE_REFERINTA_JURNAL}'], option="responsive")
    pdf.table_row(["Total document include TVA autolichidata, chiar daca furnizorul a facturat 0% TVA (reverse charge)."], option="responsive")
    pdf.output(output_path)


def genereaza_jurnal_cumparari_xlsx(jurnal: dict, output_path: str):
    """Jurnalul de cumparari in Excel, cu aceleasi coloane ca exportul din Registre."""
    df = pd.DataFrame(jurnal["randuri"]).rename(
        columns={
            "nr_crt": "Nr.Crt.",
            "data_doc": "Document Data",
            "nr_doc": "Document Numar",
            "furnizor_denumire": "Furnizor Denumire",
            "furnizor_cod_fiscal": "Furnizor Cod Fiscal",
            "total_document": "Total document (inclusiv TVA)",
            "baza": "Baza impozitare",
            "tva": "Valoare T.V.A.",
            "cod_referinta": "Referinta cod",
            "fisier": "Document justificativ (fisier)",
        }
    )
    df.to_excel(output_path, index=False)
    make_excel_pretty(output_path)


def genereaza_pachet_tva(anul: int, luna: int, setari: SetariModel | None = None) -> dict | None:
    """Genereaza intr-un singur zip documentele lunii, grupate pe codul fiscal:
    cate un folder pentru fiecare cod pe care se depun declaratii, cu prefix
    dupa tipul codului:
    - VIES-<cod> pentru codul special de TVA intracomunitar (facturile UE);
    - CIF-<cod> pentru codul normal al PFA-ului (facturile non-UE).
    Fiecare folder contine:
    - D301 completat in Markdown (si D390 VIES, pentru codul cu facturi UE);
    - jurnalul de cumparari in Excel, doar cu facturile declarate pe codul lui;
    - facturile furnizorilor (documentele justificative) pentru declaratiile din folder.
    Returneaza {'zip_path', 'd301', 'd301_lista', 'd390', 'jurnal'} sau None daca nu exista operatiuni."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    d301_lista = calculeaza_d301_lista(anul, luna, setari)
    if not d301_lista:
        return None
    d390 = calculeaza_d390(anul, luna, setari)
    jurnal = calculeaza_jurnal_cumparari(anul, luna)
    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))

    folder = get_extracts_path("tva")
    prefix = f"{anul}_{luna:02d}"
    fisiere = []  # (cale_pe_disk, cale_in_zip)

    for d301 in d301_lista:
        # Folder dedicat codului pe care se depune declaratia, cu prefix dupa tip:
        # VIES = cod TVA intracomunitar (art. 317), CIF = codul normal al PFA-ului.
        cod = d301["cif"]
        nume_folder = f"{'VIES' if _este_cod_special(setari, cod) else 'CIF'}-{cod}"
        subfolder = os.path.join(folder, nume_folder)
        os.makedirs(subfolder, exist_ok=True)

        d301_md = os.path.join(subfolder, f"D301_{prefix}.md")
        with open(d301_md, "w", encoding="utf-8") as f:
            f.write(genereaza_d301_md(d301, setari))
        fisiere.append((d301_md, f"{nume_folder}/{os.path.basename(d301_md)}"))

        if d390 and d390["cif"] == cod:
            d390_md = os.path.join(subfolder, f"D390_{prefix}.md")
            with open(d390_md, "w", encoding="utf-8") as f:
                f.write(genereaza_d390_md(d390, setari))
            fisiere.append((d390_md, f"{nume_folder}/{os.path.basename(d390_md)}"))

        # Facturile furnizorilor (documentele justificative atasate), per cod.
        nr_docs = {r["nr_doc"] for r in d301["randuri"]}
        nume_vazute = set()
        for cheltuiala in cheltuieli:
            if (cheltuiala.numar_factura or "") not in nr_docs or not cheltuiala.fisier:
                continue
            nume_factura = re.sub(r"^[A-Za-z0-9]{8}_", "", os.path.basename(cheltuiala.fisier.path))
            # Daca doua facturi au fisiere cu acelasi nume, le distingem prin numarul facturii.
            if nume_factura in nume_vazute:
                baza, ext = os.path.splitext(nume_factura)
                nume_factura = f"{baza}_{cheltuiala.numar_factura}{ext}"
            nume_vazute.add(nume_factura)
            fisiere.append(
                (cheltuiala.fisier.path, f"{nume_folder}/facturi/{nume_factura}")
            )

        # Jurnalul de cumparari doar cu facturile declarate pe acest cod.
        if jurnal:
            randuri_cod = [r for r in jurnal["randuri"] if r["nr_doc"] in nr_docs]
            jurnal_cod = {
                "anul": anul,
                "luna": luna,
                "randuri": [
                    {**r, "nr_crt": idx} for idx, r in enumerate(randuri_cod, start=1)
                ],
                "total_document": round2(sum(r["total_document"] for r in randuri_cod)),
                "total_baza": round2(sum(r["baza"] for r in randuri_cod)),
                "total_tva": round2(sum(r["tva"] for r in randuri_cod)),
            }
            jurnal_xlsx = os.path.join(subfolder, f"Jurnal_cumparari_{prefix}.xlsx")
            genereaza_jurnal_cumparari_xlsx(jurnal_cod, jurnal_xlsx)
            fisiere.append((jurnal_xlsx, f"{nume_folder}/{os.path.basename(jurnal_xlsx)}"))

    zip_path = os.path.join(get_extracts_path(), f"D301-D390_{prefix}.zip")
    with ZipFile(zip_path, "w") as zipf:
        for fp, nume_in_zip in fisiere:
            zipf.write(fp, nume_in_zip)

    return {
        "zip_path": zip_path,
        "d301": d301_lista[0],
        "d301_lista": d301_lista,
        "d390": d390,
        "jurnal": jurnal,
    }
