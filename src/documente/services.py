"""Parsarea documentelor ANAF la upload.

Rezultatul e un dictionar cu valori structurate care se pun pe
`DocumenteModel` inainte de salvare. Nu se mai scrie nimic in `save()` si nu
se mai foloseste `mentiuni` ca sursa de date pentru rapoarte.
"""

import datetime
import re

import xmltodict
from pypdf import PdfReader

from utils.decimale import D, rotund2

from .models import TipDocument


def _data(anul, luna=None):
    if not anul:
        return None
    return datetime.date(anul, luna or 1, 1)


def parseaza_document(pdf_path: str) -> dict | None:
    """Identifica tipul documentului si extrage campurile structurate."""
    if not pdf_path.lower().endswith(".pdf"):
        return None
    for parser in (recipisa_parser, pdf_parser):
        try:
            rezultat = parser(pdf_path)
        except Exception:
            rezultat = None
        if rezultat:
            return rezultat
    return None


def recipisa_parser(pdf_path: str):
    """Recipisa ANAF pentru D301/D390."""
    reader = PdfReader(pdf_path)
    pdf_text = reader.pages[0].extract_text() or ""

    tip_match = re.search(r"declara[ţt]ie\s+tip\s+(D301|D390)", pdf_text, re.IGNORECASE)
    if not tip_match:
        return None

    tip = tip_match.group(1).upper()
    perioada_match = re.search(r"perioada de raportare\s+(\d{1,2})\s+(\d{4})", pdf_text)
    cif_match = re.search(r"CIF:\s*(\d+)", pdf_text)
    index_match = re.search(
        r"Index\s+[îi]nc[ăa]rcare:\s*(\d+)\s+din\s+(\d\d\.\d\d\.\d\d\d\d)", pdf_text
    )

    anul = int(perioada_match.group(2)) if perioada_match else None
    luna = int(perioada_match.group(1)) if perioada_match else None
    cif = cif_match.group(1) if cif_match else None

    mentiuni = f"Recipisa {tip}"
    if luna and anul:
        mentiuni += f" perioada {luna:02d}/{anul}"
    if cif:
        mentiuni += f" CIF {cif}"
    if index_match:
        mentiuni += (
            f" index incarcare {index_match.group(1)} din {index_match.group(2)}"
        )
    if (
        "Nu există erori de validare" in pdf_text
        or "Nu exista erori de validare" in pdf_text
    ):
        mentiuni += " - fara erori de validare"

    return {
        "tip_document": (
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value
            if tip == "D301"
            else TipDocument.DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA.value
        ),
        "data_document": _data(anul, luna),
        "mentiuni": mentiuni,
        "tip_declaratie": tip,
        "anul": anul,
        "luna": luna,
        "cif": cif,
    }


def pdf_parser(pdf_path: str):
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    pdf_text = page.extract_text() or ""

    # D212 cu fisier XML atasat
    xml = None
    for content_list in reader.attachments.values():
        for content in content_list:
            xml = content.decode("utf-8")
            break
    if xml:
        d212_dict = xmltodict.parse(xml)
        return {
            "tip_document": TipDocument.DECLARATIE_UNICA_212.value,
            "data_document": _data(int(d212_dict["d212"]["@an_r"])),
        }

    # D212 dovada incarcare
    if "D212" in pdf_text or "declaratie unica" in pdf_text:
        data_match = re.search(
            r"Index încărcare: \d{1,} din (\d\d.\d\d.\d\d\d\d)", pdf_text, re.DOTALL
        )
        if data_match:
            data = datetime.datetime.strptime(data_match.group(1), "%d.%m.%Y").date()
            return {
                "tip_document": TipDocument.DECLARATIE_UNICA_212_DOVADA_INCARCARE.value,
                "data_document": data,
            }

    # Dovada plata taxe si impozite (ghiseul.ro)
    suma_match = re.search(r"Total valoare: (.*?) Lei", pdf_text, re.DOTALL)
    if suma_match:
        data_match = re.search(
            r"Data plății:  (\d\d.\d\d.\d\d\d\d) \d\d:\d\d:\d\d", pdf_text
        )
        if not data_match:
            return None
        data = datetime.datetime.strptime(data_match.group(1), "%d.%m.%Y").date()
        suma = D(suma_match.group(1).replace(".", "").replace(",", "."))
        return {
            "tip_document": TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value,
            "data_document": data,
            "suma_plata": rotund2(suma),
        }
    return None
