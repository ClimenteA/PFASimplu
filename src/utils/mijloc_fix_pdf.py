import os
import re
from zipfile import ZipFile

from cheltuieli.models import CheltuialaModel
from core.settings import get_extracts_path, get_media_path
from utils.decimale import format_suma
from utils.pdf import LATIME_UTILA, DocumentPdf

_COLOANE_DETALII = ((200, "left"), (LATIME_UTILA - 200, "left"))

_COLOANE_MISCARI = (
    ("Nr.inv", 38, "left"),
    ("Doc", 55, "left"),
    ("Operatiuni", 165.88, "left"),
    ("Buc", 32, "right"),
    ("Debit", 52, "right"),
    ("Credit", 52, "right"),
    ("Sold", 45, "right"),
    ("C105", 42, "right"),
)


def scrie_fisa_mijloc_fix(context: dict, cale_pdf: str) -> str:
    """Deseneaza fisa mijlocului fix si o scrie la `cale_pdf`."""

    doc = DocumentPdf()
    doc.scrie("FISA MIJLOCULUI FIX", aliniere="center", bold=True, marime=16)
    doc.spatiu(14)

    campuri = (
        ("Nr. Inventar", context["nr_inventar"]),
        ("Fel, serie, nr. data document provenienta", context["fel_document"]),
        ("Valoare de inventar", context["valoare_inventar"]),
        ("Amortizare lunara", context["amortizare_lunara"]),
        ("Denumirea mijlocului fix", "Detaliate in factura/bon."),
        ("Accesorii", "Detaliate in factura/bon."),
        ("Grupa", context["grupa"]),
        ("Codul de clasificare", context["cod_de_clasificare"]),
        ("Anul darii in folosinta", context["anul_darii_in_folosinta"]),
        ("Luna darii in folosinta", context["luna_darii_in_folosinta"]),
        ("Anul amortizarii complete", context["anul_amortizarii_complete"]),
        ("Luna amortizarii complete", context["luna_amortizarii_complete"]),
        ("Durata normala de functionare", context["durata_normala_de_functionare"]),
        ("Cota de amortizare", context["cota_de_amortizare"]),
    )
    doc.tabel(
        [("", latime, aliniere) for latime, aliniere in _COLOANE_DETALII],
        [[eticheta, str(valoare)] for eticheta, valoare in campuri],
        antet=False,
        umplere_coloana=0,
    )

    doc.spatiu(18)
    doc.scrie("Miscari", bold=True, marime=11)
    doc.spatiu(8)
    doc.tabel(list(_COLOANE_MISCARI), [[""] * len(_COLOANE_MISCARI) for _ in range(10)])

    subsol = (
        f"Fisa mijlocului fix nr. {context['nr_inventar']} - {{pagina}} / {{total}}"
    )
    return doc.salveaza(cale_pdf, subsol=subsol)


def create_fisa_mijloc_fix_pdf(db_id: int, nr_inventar: int, doar_pdf: bool = False):
    """Genereaza fisa mijlocului fix. Implicit intoarce un zip cu fisa PDF +
    documentul justificativ (folosit la download-ul Registrului-inventar).
    Cu `doar_pdf=True` intoarce doar fisa PDF (folosit la exportul pe an)."""

    inv = CheltuialaModel.objects.filter(id=db_id).first()

    fileid = os.path.basename(inv.fisier.path).split("_")[0]

    fel_document = f"{fileid} {inv.nume_cheltuiala}"

    # Nume de fisier sigur pentru sistemul de fisiere (fara spatii/caractere
    # speciale din numele cheltuielii), unic per mijloc fix. Folosit si pentru
    # zip: numele cheltuielii poate contine "/" (ex. "Laptop / birou"), care
    # altfel ar fi interpretat ca separator de directoare la scrierea zip-ului.
    nume_sigur = re.sub(r"[^\w\-.]+", "_", inv.nume_cheltuiala).strip("_")[:80]
    nume_fisa = f"fisa_mijloc_fix_{fileid}_{nume_sigur}.pdf"

    context = {
        "nr_inventar": fileid,
        "fel_document": fel_document,
        "valoare_inventar": format_suma(inv.suma_in_ron),
        "amortizare_lunara": format_suma(inv.amortizare_lunara),
        "grupa": inv.grupa,
        "cod_de_clasificare": inv.cod_de_clasificare,
        "anul_darii_in_folosinta": inv.anul_darii_in_folosinta,
        "luna_darii_in_folosinta": inv.luna_darii_in_folosinta,
        "anul_amortizarii_complete": inv.anul_amortizarii_complete,
        "luna_amortizarii_complete": inv.luna_amortizarii_complete,
        "durata_normala_de_functionare": inv.durata_normala_de_functionare,
        "cota_de_amortizare": inv.cota_de_amortizare,
    }
    save_pdf_path = os.path.join(get_media_path(), nume_fisa)
    scrie_fisa_mijloc_fix(context, save_pdf_path)

    if doar_pdf:
        return save_pdf_path

    extracts_folder = get_extracts_path()

    # Documentul justificativ poate lipsi de pe disc (sters/mutat manual):
    # in acel caz zip-ul contine doar fisa generata, in loc sa crape exportul.
    files = [save_pdf_path, inv.fisier.path]
    zip_filepath = os.path.join(extracts_folder, f"{fileid}_{nume_sigur}.zip")
    with ZipFile(zip_filepath, "w") as zipf:
        for file in files:
            if os.path.exists(file):
                zipf.write(file, os.path.basename(file))

    return zip_filepath
