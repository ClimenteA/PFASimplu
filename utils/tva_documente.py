"""Generarea documentelor TVA: XML-uri ANAF (D301/D390), PDF-uri completate,
Jurnalul de cumparari si instructiunea de plata, impachetate intr-un zip.

Structura XML urmeaza exemplurile oficiale depuse (atasate in PDF-urile semnate):
- D301: mfp:anaf:dgti:d301:declaratie:v1 (sectiune tip_operatie 4 si 5)
- D390: mfp:anaf:dgti:d390:declaratie:v3 (rezumat + operatie tip S)

Campurile nr_evid (nr. de evidenta a platii) si suma_control (totalPlata_A)
sunt generate de aplicatia oficiala ANAF la validare; aici se lasa goale/0,
iar PDF-ul generat este documentul de lucru cu toate valorile completate.
"""

import os
from xml.sax.saxutils import escape
from zipfile import ZipFile

import pandas as pd
from fpdf_table import PDFTable, Align

from core.settings import get_extracts_path, get_font_path
from setari.models import SetariModel
from utils.trezorerie import COD_BUGETAR_TVA, get_link_iban_trezorerie
from utils.tva import (
    COD_REFERINTA_JURNAL,
    DENUMIRE_REFERINTA_JURNAL,
    calculeaza_d301,
    calculeaza_d390,
    calculeaza_jurnal_cumparari,
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


def _nume_prenume_declarant(setari: SetariModel) -> tuple[str, str]:
    """Din numele complet al PFA-ului (ex. 'CLIMENTE ALIN IONEL PERSOANA FIZICA AUTORIZATA')
    se ia primul cuvant ca nume de familie, restul prenumelui (ca in exemplele depuse)."""
    nume_complet = (setari.nume or "").strip()
    for sufix in ("PERSOANA FIZICA AUTORIZATA", "PFA", "ÎNTREPRINDERE INDIVIDUALĂ", "INTREPRINDERE INDIVIDUALA"):
        if nume_complet.upper().endswith(sufix):
            nume_complet = nume_complet[: -len(sufix)].strip()
    parts = nume_complet.split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _denumire_pfa(setari: SetariModel) -> str:
    nume = (setari.nume or "").strip()
    if "PERSOANA FIZICA AUTORIZATA" in nume.upper() or nume.upper().endswith("PFA"):
        return nume
    return f"{nume} PERSOANA FIZICA AUTORIZATA"


def _adresa_declarant(setari: SetariModel) -> str:
    localitate = (setari.localitate or "").split(",")[-1].strip()
    return f"{localitate} {setari.adresa}".strip()


def genereaza_d301_xml(d301: dict, setari: SetariModel) -> str:
    nume, prenume = _nume_prenume_declarant(setari)
    attrs = (
        f'd_rec="0" an="{d301["anul"]}" luna="{d301["luna"]}" mijl_trans="0" temei="0" '
        f'cif="{escape(d301["cif"])}" denumire="{escape(_denumire_pfa(setari))}" '
        f'adresa="{escape(_adresa_declarant(setari))}" '
        f'banca="" '
        f'cont="{escape(setari.get_iban_pentru_valuta("RON") or "")}" pers_inreg="2" nr_evid="" '
        f'baza1="0" tva1="0" baza2="0" tva2="0" baza3="0" tva3="0" '
        f'baza4="{_fmt_num(d301["baza4"])}" tva4="{_fmt_num(d301["tva4"])}" '
        f'baza5="{_fmt_num(d301["baza5"])}" tva5="{_fmt_num(d301["tva5"])}" totalPlata_A="0" '
        f'nume_declarant="{escape(nume)}" prenume_declarant="{escape(prenume)}" functia_declarant="TITULAR"'
    )
    linii = [
        '<?xml version="1.0"?>',
        f'<declaratie301 {attrs} '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="mfp:anaf:dgti:d301:declaratie:v1 D301.xsd" '
        'xmlns="mfp:anaf:dgti:d301:declaratie:v1">',
    ]
    for r in d301["randuri"]:
        linii.append(
            f'<sectiune tip_operatie="{r["tip_operatie"]}" nr_doc="{escape(r["nr_doc"])}" '
            f'data_doc="{r["data_doc"]}" val_valuta="{_fmt_num(r["val_valuta"])}" '
            f'tip_valuta="{r["tip_valuta"]}" curs_valutar="{_fmt_num(r["curs_valutar"])}" '
            f'baza="{_fmt_num(r["baza"])}" tva="{_fmt_num(r["tva"])}"/>'
        )
    linii.append("</declaratie301>")
    return "\n".join(linii)


def genereaza_d390_xml(d390: dict, setari: SetariModel) -> str:
    nume, prenume = _nume_prenume_declarant(setari)
    attrs = (
        f'luna="{d390["luna"]:02d}" an="{d390["anul"]}" d_rec="0" '
        f'nume_declar="{escape(nume)}" prenume_declar="{escape(prenume)}" functie_declar="TITULAR" '
        f'cui="{escape(d390["cif"])}" den="{escape(_denumire_pfa(setari))}" '
        f'adresa="{escape(_adresa_declarant(setari))}" totalPlata_A="0"'
    )
    linii = [
        '<?xml version="1.0"?>',
        f'<declaratie390 {attrs} '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="mfp:anaf:dgti:d390:declaratie:v3 D390.xsd" '
        'xmlns="mfp:anaf:dgti:d390:declaratie:v3">',
        f'<rezumat nr_pag="1" nrOPI="{d390["nr_operatori"]}" bazaL="0" bazaT="0" bazaA="0" '
        f'bazaP="0" bazaS="{d390["bazaS"]}" bazaR="0" total_baza="{d390["total_baza"]}" />',
    ]
    for r in d390["randuri"]:
        linii.append(
            f'<operatie tip="{r["tip"]}" tara="{r["tara"]}" codO="{escape(r["cod_operator"])}" '
            f'denO="{escape(r["denumire_operator"])}" baza="{r["baza"]}" />'
        )
    linii.append("</declaratie390>")
    return "\n".join(linii)


def _pdf_nou() -> PDFTable:
    pdf = PDFTable()
    pdf.add_fonts_custom(
        font_name="arial",
        font_extension="ttf",
        font_dir=get_font_path(),
        set_default=True,
    )
    return pdf


def _pdf_antet(pdf: PDFTable, titlu: str, setari: SetariModel, cif: str, anul: int, luna: int):
    pdf.table_header([titlu], align=Align.L)
    pdf.table_row([""])
    pdf.table_row([f"Perioada de raportare: luna {luna:02d} / anul {anul}"])
    pdf.table_row([f"Cod de identificare fiscala: RO{cif}"])
    pdf.table_row([f"Denumire: {_denumire_pfa(setari)}"], option="responsive")
    pdf.table_row([f"Domiciliul fiscal: {_adresa_declarant(setari)}"], option="responsive")
    pdf.table_row([f"Banca / Cont: {setari.get_iban_pentru_valuta('RON') or '-'}"], option="responsive")
    pdf.table_row(["Calitate: Persoane inregistrate conform art. 317 din Legea nr. 227/2015 (cod TVA intracomunitar)"], option="responsive")
    pdf.table_row(["Declaratie rectificativa: NU"])
    pdf.table_row([""])


def genereaza_d301_pdf(d301: dict, setari: SetariModel, output_path: str):
    pdf = _pdf_nou()
    _pdf_antet(pdf, "D301 - DECONT SPECIAL DE TAXA PE VALOAREA ADAUGATA", setari, d301["cif"], d301["anul"], d301["luna"])

    width_cols = pdf.table_cols(0.7, 3.2, 1.6, 1, 1.4, 1.6, 1.4)
    header = ["Nr.", "Document Numar/Data", "Valoare valuta", "Tip", "Curs schimb", "Baza impozitare", "TVA datorat"]

    for sectiune, titlu, tip in [
        ("4", "Sectiunea 4. Operatiuni prevazute la art. 307 alin. (2), (3), (5) si (6) - lei -", "4"),
        ("5", "Sectiunea 4.1. Achizitii de servicii intracomunitare cf. art. 307 alin. (2) - lei -", "5"),
    ]:
        pdf.set_font(pdf.font, "B", pdf.text_normal_size)
        pdf.table_row([titlu], option="responsive")
        pdf.set_font(pdf.font, "", pdf.text_normal_size)
        pdf.table_header(header, width_cols, align=Align.C)
        randuri = [r for r in d301["randuri"] if r["tip_operatie"] == tip]
        for r in randuri:
            pdf.table_row(
                [
                    str(r["nr_crt"]),
                    f'{r["nr_doc"]} / {r["data_doc"]}',
                    _fmt_num(r["val_valuta"]),
                    r["tip_valuta"],
                    _fmt_num(r["curs_valutar"]),
                    f'{r["baza"]:.2f}',
                    f'{r["tva"]:.2f}',
                ],
                width_cols,
                option="responsive",
            )
        if not randuri:
            pdf.table_row(["-", "0", "0", "-", "-", "0.00", "0.00"], width_cols)
        pdf.set_font(pdf.font, "B", pdf.text_normal_size)
        pdf.table_row(
            ["", "TOTAL", "", "", "", f'{d301[f"baza{sectiune}"]:.2f}', f'{d301[f"tva{sectiune}"]:.2f}'],
            width_cols,
        )
        pdf.set_font(pdf.font, "", pdf.text_normal_size)
        pdf.table_row([""])

    pdf.table_row(["Sectiunile 1-3: zero (fara achizitii intracomunitare de bunuri, mijloace de transport noi sau produse accizabile)."], option="responsive")
    pdf.table_row(["Atentie! Facturile declarate in Sectiunea 4.1 trebuie declarate si in Sectiunea 4!"], option="responsive")
    pdf.table_row([""])
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)
    pdf.table_row([f'TVA de plata: {d301["total_de_plata"]:.2f} lei'], option="responsive")
    pdf.set_font(pdf.font, "", pdf.text_normal_size)
    pdf.table_row([f'Termen depunere si plata: {d301["termen"].strftime("%d.%m.%Y")}'])
    pdf.table_row(["Suma de control si Nr. de evidenta a platii se genereaza de aplicatia oficiala ANAF la validare."], option="responsive")
    pdf.output(output_path)


def genereaza_d390_pdf(d390: dict, setari: SetariModel, output_path: str):
    pdf = _pdf_nou()
    _pdf_antet(pdf, "D390 VIES - DECLARATIE RECAPITULATIVA", setari, d390["cif"], d390["anul"], d390["luna"])

    pdf.table_row([f'Numar total operatori intracomunitari: {d390["nr_operatori"]}'])
    pdf.table_row([""])
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)
    pdf.table_row(["Rezumatul declaratiei (lei)"], option="responsive")
    pdf.set_font(pdf.font, "", pdf.text_normal_size)
    pdf.table_row([f'L (livrari bunuri): 0 | T (triunghiulare): 0 | A (achizitii bunuri): 0 | P (prestari servicii): 0 | S (achizitii servicii): {d390["bazaS"]} | R (agricultori): 0'], option="responsive")
    pdf.table_row([""])

    width_cols = pdf.table_cols(0.7, 0.7, 2, 2.2, 4, 1.6)
    pdf.table_header(["Nr.", "Tip", "Tara", "Cod operator", "Denumire operator", "Baza impozabila"], width_cols, align=Align.C)
    for r in d390["randuri"]:
        pdf.table_row(
            [
                str(r["nr_crt"]),
                r["tip"],
                f'{r["tara_denumire"]}-{r["tara"]}',
                r["cod_operator"],
                r["denumire_operator"],
                str(r["baza"]),
            ],
            width_cols,
            option="responsive",
        )
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)
    pdf.table_row(["", "", "", "", "TOTAL GENERAL", str(d390["total_baza"])], width_cols)
    pdf.set_font(pdf.font, "", pdf.text_normal_size)
    pdf.table_row([""])
    pdf.table_row(["Codul operatorului se scrie fara prefixul de tara (tara este coloana separata)."], option="responsive")
    pdf.table_row([f'Termen depunere: {d390["termen"].strftime("%d.%m.%Y")}'])
    pdf.output(output_path)


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


def genereaza_jurnal_cumparari_csv(jurnal: dict, output_path: str):
    df = pd.DataFrame(jurnal["randuri"])
    df = df.rename(
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
        }
    )
    df.to_csv(output_path, index=False)


def genereaza_instructiune_plata(d301: dict, setari: SetariModel, output_path: str):
    pdf = _pdf_nou()
    pdf.table_header(["INSTRUCTIUNE DE PLATA TVA - D301"], align=Align.L)
    pdf.table_row([""])
    pdf.table_row([f'Perioada: {LUNI_RO[d301["luna"]]} {d301["anul"]}'])
    pdf.table_row([f'Suma de plata: {d301["total_de_plata"]:.2f} lei'])
    pdf.table_row([f'Termen de plata: {d301["termen"].strftime("%d.%m.%Y")} (25 inclusiv a lunii urmatoare)'])
    pdf.table_row([""])
    pdf.table_row(["Beneficiar: Trezoreria Statului (trezoreria operativa de domiciliul fiscal)"], option="responsive")
    pdf.table_row([f'IBAN beneficiar: {setari.cont_iban_trezoreria or "NECOMPLETAT - vezi Setari"}'])
    pdf.table_row([f'Cod bugetar: {COD_BUGETAR_TVA} - TVA incasata pentru operatiuni interne'])
    pdf.table_row([f'Cod identificare fiscala platitor: {d301["cif"]}'])
    pdf.table_row([f'Explicatie plata: TVA D301 {LUNI_RO[d301["luna"]]} {d301["anul"]}'])
    pdf.table_row([""])
    pdf.table_row(["NU se plateste in contul unic. TVA din D301 se plateste in contul 20A100101 al trezoreriei."], option="responsive")
    pdf.table_row([f'Lista IBAN-uri ANAF: {get_link_iban_trezorerie(setari.localitate)}'], option="responsive")
    pdf.output(output_path)


def genereaza_pachet_tva(anul: int, luna: int, setari: SetariModel | None = None) -> dict | None:
    """Genereaza intr-un singur zip toate documentele lunii:
    D301 (PDF + XML), D390 (PDF + XML, doar daca exista UE),
    Jurnal de cumparari (PDF + CSV) si instructiunea de plata.
    Returneaza {'zip_path', 'd301', 'd390', 'jurnal'} sau None daca nu exista operatiuni."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    d301 = calculeaza_d301(anul, luna, setari)
    if not d301:
        return None
    d390 = calculeaza_d390(anul, luna, setari)
    jurnal = calculeaza_jurnal_cumparari(anul, luna)

    folder = get_extracts_path("tva")
    prefix = f"{anul}_{luna:02d}"
    fisiere = []

    d301_pdf = os.path.join(folder, f"D301_{prefix}.pdf")
    genereaza_d301_pdf(d301, setari, d301_pdf)
    fisiere.append(d301_pdf)

    d301_xml = os.path.join(folder, f"D301_{prefix}.xml")
    with open(d301_xml, "w", encoding="utf-8") as f:
        f.write(genereaza_d301_xml(d301, setari))
    fisiere.append(d301_xml)

    if d390:
        d390_pdf = os.path.join(folder, f"D390_{prefix}.pdf")
        genereaza_d390_pdf(d390, setari, d390_pdf)
        fisiere.append(d390_pdf)

        d390_xml = os.path.join(folder, f"D390_{prefix}.xml")
        with open(d390_xml, "w", encoding="utf-8") as f:
            f.write(genereaza_d390_xml(d390, setari))
        fisiere.append(d390_xml)

    if jurnal:
        jurnal_pdf = os.path.join(folder, f"Jurnal_cumparari_{prefix}.pdf")
        genereaza_jurnal_cumparari_pdf(jurnal, setari, jurnal_pdf)
        fisiere.append(jurnal_pdf)

        jurnal_csv = os.path.join(folder, f"Jurnal_cumparari_{prefix}.csv")
        genereaza_jurnal_cumparari_csv(jurnal, jurnal_csv)
        fisiere.append(jurnal_csv)

    plata_pdf = os.path.join(folder, f"Instructiune_plata_TVA_{prefix}.pdf")
    genereaza_instructiune_plata(d301, setari, plata_pdf)
    fisiere.append(plata_pdf)

    zip_path = os.path.join(get_extracts_path(), f"D301-D390_{prefix}.zip")
    with ZipFile(zip_path, "w") as zipf:
        for fp in fisiere:
            zipf.write(fp, os.path.basename(fp))

    return {"zip_path": zip_path, "d301": d301, "d390": d390, "jurnal": jurnal}
