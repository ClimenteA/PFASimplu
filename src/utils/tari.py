"""Tari pentru furnizorii externi (achizitii de servicii cu taxare inversa).

UE/non-UE se deduce automat din tara furnizorului:
- UE: se depun D301 (sectiunile 4 si 4.1) + D390 VIES (tip S);
- non-UE: se depune doar D301 (sectiunea 4), fara D390.

Lista statelor membre UE urmeaza sursa oficiala (27 de state, fara Romania -
furnizorii romani se inregistreaza cu originea "Romania"):
https://european-union.europa.eu/node/288/rss_ro

Regatul Unit este tara non-UE dupa Brexit.
"""

# cod ISO -> (denumire, este_ue)
TARI = {
    "AT": ("Austria", True),
    "BE": ("Belgia", True),
    "BG": ("Bulgaria", True),
    "CY": ("Cipru", True),
    "CZ": ("Cehia", True),
    "DE": ("Germania", True),
    "DK": ("Danemarca", True),
    "EE": ("Estonia", True),
    "ES": ("Spania", True),
    "FI": ("Finlanda", True),
    "FR": ("Franta", True),
    "GR": ("Grecia", True),
    "HR": ("Croatia", True),
    "HU": ("Ungaria", True),
    "IE": ("Irlanda", True),
    "IT": ("Italia", True),
    "LT": ("Lituania", True),
    "LU": ("Luxemburg", True),
    "LV": ("Letonia", True),
    "MT": ("Malta", True),
    "NL": ("Olanda", True),
    "PL": ("Polonia", True),
    "PT": ("Portugalia", True),
    "SE": ("Suedia", True),
    "SI": ("Slovenia", True),
    "SK": ("Slovacia", True),
    # Non-UE
    "AU": ("Australia", False),
    "CA": ("Canada", False),
    "CH": ("Elvetia", False),
    "CN": ("China", False),
    "GB": ("Marea Britanie (non-UE)", False),
    "IL": ("Israel", False),
    "IN": ("India", False),
    "JP": ("Japonia", False),
    "KR": ("Coreea de Sud", False),
    "MD": ("Moldova", False),
    "NO": ("Norvegia", False),
    "NZ": ("Noua Zeelanda", False),
    "RS": ("Serbia", False),
    "SG": ("Singapore", False),
    "TR": ("Turcia", False),
    "UA": ("Ucraina", False),
    "US": ("SUA", False),
    "AE": ("Emiratele Arabe Unite", False),
    "ZA": ("Africa de Sud", False),
    "BR": ("Brazilia", False),
    "MX": ("Mexic", False),
}

# Liste pentru dropdown-uri, filtrate dupa originea furnizorului:
# "Servicii din UE" arata doar tarile UE, "Servicii din afara UE" doar non-UE.
TARI_UE_CHOICES = [
    (cod, f"{cod} - {denumire}")
    for cod, (denumire, ue) in sorted(TARI.items(), key=lambda kv: kv[1][0])
    if ue
]
TARI_NON_UE_CHOICES = [
    (cod, f"{cod} - {denumire}")
    for cod, (denumire, ue) in sorted(TARI.items(), key=lambda kv: kv[1][0])
    if not ue
]
TARI_CHOICES = TARI_UE_CHOICES + TARI_NON_UE_CHOICES


def este_tara_ue(cod_tara: str) -> bool:
    cod = (cod_tara or "").strip().upper()
    return TARI.get(cod, ("", False))[1]


def denumire_tara(cod_tara: str) -> str:
    cod = (cod_tara or "").strip().upper()
    return TARI.get(cod, (cod, False))[0]
