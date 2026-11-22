"""Scraper pentru IBAN-urile trezoreriilor (plata TVA, cod bugetar 20A100101).

Sursa oficiala ANAF:
https://www.anaf.ro/anaf/internet/ANAF/asistenta_contribuabili/plata_oblig_fiscale/coduri_iban

Pagina listeaza trezoreriile judetene (TREZxxx) cu linkuri catre:
- pagini .htm pe judet, care listeaza trezoreriile operative cu PDF-uri
  (ex. Iasi.htm -> iban_TREZ405_TREZ406.pdf pentru Municipiul Iasi);
- PDF-uri directe pentru Bucuresti (sectoare) si Municipiul Bucuresti.

In PDF-uri, IBAN-urile pentru TVA au codul bugetar 20A100101 in corpul IBAN-ului
(ex. RO41TREZ40620A100101XTVA), deci le putem extrage cu regex si le asociem
trezoreriei din antetul paginii ("Trezorerie operativa Municipiul Iasi").

Rulare manuala: python utils/scrape_iban_trezorerie.py
Rulare automata: la salvarea Setarilor, daca static/iban_trezorerie.json lipseste
(vezi utils/trezorerie.py: asigura_date_iban_trezorerie).
Rezultat: static/iban_trezorerie.json (date statice, verificate la build).
"""

import io
import json
import os
import re
import sys
import time

import requests
from pypdf import PdfReader
from unidecode import unidecode

ANAF_CODURI_IBAN = (
    "https://www.anaf.ro/anaf/internet/ANAF/asistenta_contribuabili/"
    "plata_oblig_fiscale/coduri_iban"
)
STATIC_IBAN_BASE = "https://static.anaf.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/"
COD_BUGETAR_TVA = "20A100101"

def get_output_path() -> str:
    """Calea de scriere a JSON-ului: static/ in dezvoltare,
    _internal/static/ in executabilul PyInstaller (folderul static e read-only
    in unele instalari; _internal este langa executabil si scriibil)."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyinstaller_static = os.path.join(base, "_internal", "static")
    if os.path.isdir(pyinstaller_static):
        return os.path.join(pyinstaller_static, "iban_trezorerie.json")
    return os.path.join(base, "static", "iban_trezorerie.json")


OUTPUT_PATH = get_output_path()

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (PFASimplu IBAN scraper)"})


def fetch(url: str) -> bytes:
    for incercare in range(3):
        try:
            r = SESSION.get(url, timeout=60)
            r.raise_for_status()
            return r.content
        except Exception as err:
            if incercare == 2:
                raise
            print(f"  retry {url}: {err}")
            time.sleep(2)


def normalizeaza(text: str) -> str:
    """Cheie de comparare: fara diacritice, lowercase, spatii simple."""
    text = unidecode(text or "")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def extrage_localitate_din_nume(nume_trezorerie: str) -> str:
    """Din 'Trezorerie operativa Municipiul Tg.Frumos' -> 'targu frumos'.
    Cheia trebuie sa se potriveasca cu localitatile din utils/localitati.py."""
    nume = normalizeaza(nume_trezorerie)
    nume = re.sub(r"^trezoreri[ae] (operativa|judeteana) ", "", nume)
    nume = re.sub(r"^(municipiul|municipiu|orasul|oras|comunala) ", "", nume)
    # Abrevieri din PDF-urile ANAF
    nume = nume.replace("tg.", "targu ").replace("sf.", "sfantul ")
    nume = nume.replace("campulung m.", "campulung moldovenesc")
    nume = nume.replace("drobeta tr.severin", "drobeta turnu severin")
    nume = nume.replace("sighetul-marmatiei", "sighetu marmatiei")
    nume = nume.replace("odorheiul secuiesc", "odorheiu secuiesc")
    nume = nume.replace("chisinau cris", "chisineu cris")
    nume = re.sub(r"\s+", " ", nume).strip()
    return nume


def extrage_ibanuri_tva_din_pdf(pdf_bytes: bytes) -> dict[str, dict]:
    """Intoarce {cod_trezorerie: {nume, iban, sursa}} pentru conturile 20A100101.

    IBAN-urile TVA au codul bugetar in corp: ROxxTREZccc20A100101...
    Numele trezoreriei se ia din antetul fiecarei pagini
    ("Trezorerie operativa Municipiul Iasi"). Un PDF poate acoperi mai multe
    trezorerii (ex. TREZ405 + TREZ406), fiecare pe paginile ei."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    rezultat = {}
    for page in reader.pages:
        text = page.extract_text() or ""
        # Antetul paginii: "...Trezorerie operativa Municipiul Iasi" sau
        # "Trezoreria operativa ..." / "Trezoreria judeteana ..."
        nume_match = re.search(
            r"(Trezoreri[ae]\s+(?:operativ[ăa]|jude[țt]ean[ăa])\s+[^\n]+)",
            text,
        )
        nume = nume_match.group(1).strip() if nume_match else ""
        nume = re.sub(r"\s+", " ", nume)

        for iban in re.findall(r"RO\d{2}TREZ\d{3}" + COD_BUGETAR_TVA + r"[A-Z0-9]*", text):
            cod_trez = re.match(r"RO\d{2}(TREZ\d{3})", iban).group(1)
            if cod_trez not in rezultat:
                rezultat[cod_trez] = {"nume": nume, "iban": iban}
    return rezultat


def scrape(verbose: bool = True) -> list[dict]:
    def log(msg):
        if verbose:
            print(msg)

    log(f"Descarc pagina principala: {ANAF_CODURI_IBAN}")
    html = fetch(ANAF_CODURI_IBAN).decode("utf-8", errors="replace")

    # Linkuri catre paginile .htm pe judet si PDF-urile directe (Bucuresti)
    linkuri_htm = sorted(set(re.findall(
        r"https://static\.anaf\.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/[A-Za-z_]+\.htm",
        html,
    )))
    linkuri_pdf_directe = sorted(set(re.findall(
        r"https://static\.anaf\.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/iban_TREZ\d+_TREZ\d+\.pdf",
        html,
    )))

    # PDF-urile operative de pe paginile judetelor
    pdfuri = {}  # url -> context (nume judet / nume trezorerie din link)
    for url_htm in linkuri_htm:
        judet = url_htm.rsplit("/", 1)[-1].removesuffix(".htm").replace("_", " ")
        log(f"Judet: {judet} ({url_htm})")
        try:
            html_judet = fetch(url_htm).decode("windows-1252", errors="replace")
        except Exception as err:
            log(f"  EROARE la {url_htm}: {err}")
            continue
        for m in re.finditer(
            r'href="(https?://static\.anaf\.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/(iban_TREZ\d+_TREZ\d+\.pdf))"[^>]*>\s*(?:<[^>]+>|\s)*([^<]+)',
            html_judet,
        ):
            url_pdf = m.group(1).replace("http://", "https://")
            nume_link = re.sub(r"\s+", " ", m.group(3)).strip()
            pdfuri[url_pdf] = {"judet": judet, "nume_link": nume_link}
        time.sleep(0.3)

    for url_pdf in linkuri_pdf_directe:
        pdfuri.setdefault(url_pdf, {"judet": "Bucuresti", "nume_link": ""})

    log(f"\nTotal PDF-uri de procesat: {len(pdfuri)}")
    randuri = []
    for url_pdf, context in sorted(pdfuri.items()):
        log(f"PDF: {url_pdf.rsplit('/', 1)[-1]} ({context['nume_link'] or context['judet']})")
        try:
            pdf_bytes = fetch(url_pdf)
            ibanuri = extrage_ibanuri_tva_din_pdf(pdf_bytes)
        except Exception as err:
            log(f"  EROARE: {err}")
            continue
        for cod_trez, date in ibanuri.items():
            nume = date["nume"] or context["nume_link"]
            randuri.append({
                "judet": context["judet"],
                "cod_trezorerie": cod_trez,
                "nume_trezorerie": nume,
                "localitate": extrage_localitate_din_nume(nume),
                "iban": date["iban"],
                "cod_bugetar": COD_BUGETAR_TVA,
                "sursa": url_pdf,
            })
        time.sleep(0.3)

    # Deduplicare pe (cod_trezorerie, iban)
    vazute = set()
    unice = []
    for r in randuri:
        cheie = (r["cod_trezorerie"], r["iban"])
        if cheie not in vazute:
            vazute.add(cheie)
            unice.append(r)
    return unice


def salveaza_json(randuri: list[dict], output_path: str | None = None) -> str:
    """Scrie tabelul de trezorerii in JSON (atomic: fisier temporar + rename)."""
    output_path = output_path or get_output_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sursa": ANAF_CODURI_IBAN,
                "cod_bugetar": COD_BUGETAR_TVA,
                "generat_la": time.strftime("%Y-%m-%d"),
                "trezorerii": sorted(randuri, key=lambda r: (r["judet"], r["nume_trezorerie"])),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    os.replace(tmp_path, output_path)
    return output_path


def main():
    randuri = scrape()
    print(f"\nTotal trezorerii cu IBAN TVA: {len(randuri)}")
    if not randuri:
        print("EROARE: nu s-a extras niciun IBAN; nu suprascriu fisierul existent.")
        return 1
    output_path = salveaza_json(randuri)
    print(f"Scris: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
