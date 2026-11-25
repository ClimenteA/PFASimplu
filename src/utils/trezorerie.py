"""Link-uri si IBAN-uri pentru trezoreriile ANAF (plata TVA, cod bugetar 20A100101).

Datele din static/iban_trezorerie.json au fost extrase din sursele oficiale ANAF
(scraper: utils/scrape_iban_trezorerie.py):
https://www.anaf.ro/anaf/internet/ANAF/asistenta_contribuabili/plata_oblig_fiscale/coduri_iban

Cand utilizatorul selecteaza localitatea in Setari, aplicatia stie automat
IBAN-ul trezoreriei pentru plata TVA. Linkul sursei (PDF-ul ANAF) ramane
afisat ca utilizatorul sa poata verifica.

TVA din D301 NU se plateste in contul unic.
"""

import json
import os
import re
from functools import lru_cache

from unidecode import unidecode

ANAF_IBAN_BASE = "https://static.anaf.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/"
ANAF_CODURI_IBAN = (
    "https://www.anaf.ro/anaf/internet/ANAF/asistenta_contribuabili/"
    "plata_oblig_fiscale/coduri_iban"
)

COD_BUGETAR_TVA = "20A100101"

_JSON_PATHS = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static",
        "iban_trezorerie.json",
    ),
    # Calea din executabilul PyInstaller (_internal/static)
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "_internal",
        "static",
        "iban_trezorerie.json",
    ),
]


def _norm(text: str) -> str:
    text = unidecode(text or "")
    text = re.sub(r"[\s\-]+", " ", text).strip().lower()
    return text


@lru_cache(maxsize=1)
def _get_trezorerii() -> list[dict]:
    for path in _JSON_PATHS:
        try:
            with open(path, "r", encoding="utf-8") as f:
                date = json.load(f).get("trezorerii", [])
                if date:
                    return date
        except (OSError, json.JSONDecodeError):
            continue
    return []


def asigura_date_iban_trezorerie() -> bool:
    """Daca tabelul iban_trezorerie.json lipseste (sau e gol/corupt), ruleaza
    scraper-ul ANAF si il genereaza. Se apeleaza la salvarea Setarilor.

    Intoarce True daca datele sunt disponibile (existente sau proaspat descarcate),
    False daca descarcarea a esuat (lipsa retea etc.) - salvarea Setarilor
    continua oricum, doar fara IBAN automat.
    """
    if _get_trezorerii():
        return True

    # Import local: scraper-ul trage requests/pypdf doar cand e nevoie.
    from utils.scrape_iban_trezorerie import scrape, salveaza_json

    try:
        randuri = scrape(verbose=False)
        if not randuri:
            return False
        salveaza_json(randuri)
    except Exception:
        return False

    _get_trezorerii.cache_clear()
    return bool(_get_trezorerii())


def get_judet_din_localitate(localitate: str) -> str | None:
    """Extrage numele judetului din formatul "RO-IS, jud. Iasi, Iasi"."""
    if not localitate:
        return None
    match = re.search(r"jud\.\s*([A-Za-z\- ]+)", localitate)
    if not match:
        return None
    return match.group(1).strip()


def get_nume_localitate(localitate: str) -> str | None:
    """Extrage numele localitatii din "RO-IS, jud. Iasi, Iasi" -> "Iasi".
    Pentru "RO-NT, jud. Neamt, com. Piatra Neamt, Piatra-Neamt" -> "Piatra-Neamt"
    (ultimul segment este localitatea efectiva)."""
    if not localitate:
        return None
    parts = [p.strip() for p in localitate.split(",")]
    if len(parts) < 3:
        return None
    return parts[-1]


def get_iban_trezorerie_pentru_localitate(localitate: str) -> dict | None:
    """Cauta IBAN-ul trezoreriei pentru plata TVA pe baza localitatii din Setari.

    Intoarce {iban, nume_trezorerie, cod_trezorerie, sursa} sau None.
    Potrivirea se face pe judet + numele localitatii (fara diacritice,
    cu variante comuna/oras si abrevieri ANAF: Tg., Sf. etc.)."""
    judet = get_judet_din_localitate(localitate)
    nume_loc = get_nume_localitate(localitate)
    if not judet or not nume_loc:
        return None

    judet_n = _norm(judet)
    loc_n = _norm(nume_loc)

    candidati = [
        t for t in _get_trezorerii() if _norm(t["judet"]) == judet_n
    ]
    if not candidati:
        return None

    # Bucuresti: sectoarele au trezorerii proprii (TREZ701-706)
    if judet_n == "bucuresti":
        sector_match = re.search(r"sector\s*(\d)", loc_n)
        if sector_match:
            sector = f"sector {sector_match.group(1)}"
            for t in candidati:
                if _norm(t["localitate"]) == sector:
                    return t
        # Localitate fara sector -> Trezoreria Municipiul Bucuresti
        for t in candidati:
            if _norm(t["localitate"]) == "bucuresti":
                return t
        return None

    # Potrivire exacta pe localitate
    for t in candidati:
        if _norm(t["localitate"]) == loc_n:
            return t

    # Variante: "Sfantu Gheorghe" vs "Sfantul Gheorghe", "Targu X" vs "Tirgu X",
    # "Simleu Silvaniei" vs "Simleul Silvaniei", "Otelu Rosu" vs "Otelul Rosu",
    # "Viseu de Sus" vs "Viseul de Sus"
    variante = {loc_n}
    perechi = [
        ("sfantul ", "sfantu "),
        ("targu ", "tirgu "),
        ("simleul ", "simleu "),
        ("otelul ", "otelu "),
        ("viseul ", "viseu "),
    ]
    for v in list(variante):
        for lung, scurt in perechi:
            if lung in v:
                variante.add(v.replace(lung, scurt))
            if scurt in v:
                variante.add(v.replace(scurt, lung))
    for t in candidati:
        if _norm(t["localitate"]) in variante:
            return t

    # Localitatea e o parte a orasului cu trezorerie proprie
    # (ex. "Eforie Nord" -> "Eforie", "Poiana Brasov" -> "Brasov" via comuna).
    # Potrivim doar pe PRIMUL cuvant al numelui si doar daca rezultatul e unic.
    # Nu potrivim pe cuvinte interioare: "Boiu Mare" nu e Baia Mare,
    # "Cristuru Secuiesc" nu e Odorheiu Secuiesc.
    primul_cuvant = loc_n.split()[0]
    if len(primul_cuvant) >= 4:
        potriviri = [
            t for t in candidati
            if _norm(t["localitate"]).split()[0] == primul_cuvant
        ]
        if len(potriviri) == 1:
            return potriviri[0]

    # Cazul "com. Tirgu Carbunesti, Carbunesti" sau "com. Piatra Neamt, Piatra-Neamt":
    # satul apartine orasului cu trezorerie. Folosim numele COMUNEI doar daca
    # localitatea efectiva seamana cu el (un cuvant semnificativ comun) - altfel
    # un sat oarecare din comuna nu trebuie sa primeasca IBAN-ul orasului resedinta.
    parts = [p.strip() for p in (localitate or "").split(",")]
    if len(parts) >= 4 and parts[-2].lower().startswith("com."):
        nume_comuna = _norm(parts[-2][4:].strip())
        cuvinte_loc = {c for c in loc_n.split() if len(c) >= 4}
        cuvinte_comuna = {c for c in nume_comuna.split() if len(c) >= 4}
        if cuvinte_loc & cuvinte_comuna:
            for t in candidati:
                if _norm(t["localitate"]) == nume_comuna:
                    return t
            variante_comuna = {nume_comuna}
            for v in list(variante_comuna):
                for lung, scurt in perechi:
                    if lung in v:
                        variante_comuna.add(v.replace(lung, scurt))
                    if scurt in v:
                        variante_comuna.add(v.replace(scurt, lung))
            for t in candidati:
                if _norm(t["localitate"]) in variante_comuna:
                    return t

    # Fallback: trezoreria judeteana (contul de venituri al judetului).
    # Nu o returnam automat - localitatile rurale sunt arondate unei trezorerii
    # operative pe care nu o putem deduce sigur; utilizatorul verifica linkul.
    return None


def get_link_iban_trezorerie(localitate: str) -> str:
    """Link-ul ANAF cu lista IBAN-urilor trezoreriilor pentru judetul PFA-ului.
    Daca stim trezoreria exacta, intoarcem PDF-ul ei (sursa IBAN-ului)."""
    potrivire = get_iban_trezorerie_pentru_localitate(localitate)
    if potrivire:
        return potrivire["sursa"]

    judet = get_judet_din_localitate(localitate)
    if not judet:
        return ANAF_CODURI_IBAN

    # Paginile pe judet din lista ANAF (verificate); exceptii cu underscore.
    judet_norm = _norm(judet)
    if judet_norm == "bucuresti":
        return ANAF_IBAN_BASE + "iban_TREZ000_TREZ700.pdf"

    pagina = unidecode(judet).strip().replace(" ", "_").replace("-", "_")
    return ANAF_IBAN_BASE + pagina + ".htm"
