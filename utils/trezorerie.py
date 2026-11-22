"""Link-uri catre listele oficiale ANAF cu IBAN-urile trezoreriilor,
pe baza localitatii PFA-ului (format "RO-IS, jud. Iasi, Iasi").

Utilizatorul cauta in PDF-ul trezoreriei operative de localitatea lui randul
cu codul bugetar 20A100101 (TVA incasata pentru operatiuni interne).
TVA din D301 NU se plateste in contul unic.
"""

import re
from unidecode import unidecode

ANAF_IBAN_BASE = "https://static.anaf.ro/static/10/Anaf/AsistentaContribuabili_r/iban2014/"
ANAF_ASISTENTA = "https://static.anaf.ro/static/10/Anaf/AsistentaContribuabili_r/AsistentaContribuabili.html"

COD_BUGETAR_TVA = "20A100101"

# Judetele au pagini "<Nume>.htm" pe site-ul ANAF (verificate).
# Exceptii: Satu Mare -> Satu_Mare.htm, Caras-Severin -> Caras_Severin.htm.
# Pentru Bistrita-Nasaud si Bucuresti nu exista pagina dedicata in iban2014;
# acolo trimitem utilizatorul la pagina generala de asistenta ANAF.
JUDETE_FARA_PAGINA = {"bistrita-nasaud", "bucuresti"}


def get_judet_din_localitate(localitate: str) -> str | None:
    """Extrage numele judetului din formatul "RO-IS, jud. Iasi, Iasi"."""
    if not localitate:
        return None
    match = re.search(r"jud\.\s*([A-Za-z\- ]+)", localitate)
    if not match:
        return None
    return match.group(1).strip()


def get_link_iban_trezorerie(localitate: str) -> str:
    """Link-ul ANAF cu lista IBAN-urilor trezoreriilor pentru judetul PFA-ului."""
    judet = get_judet_din_localitate(localitate)
    if not judet:
        return ANAF_ASISTENTA

    judet_norm = unidecode(judet).strip().lower()
    if judet_norm in JUDETE_FARA_PAGINA:
        return ANAF_ASISTENTA

    # "Satu Mare" -> "Satu_Mare", "Caras-Severin" -> "Caras_Severin"
    pagina = unidecode(judet).strip().replace(" ", "_").replace("-", "_")
    return ANAF_IBAN_BASE + pagina + ".htm"
