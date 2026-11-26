"""Parametri fiscali pe ani, cititi din JSON-ul din ``src/static/``.

Fisierul are o cheie per an; fiecare an contine doar valorile care se schimba.
Pentru un an cerut, parametrii se construiesc prin suprapunerea anilor
disponibili, de la cel mai vechi la cel mai nou care nu depasesc anul cerut.
Un parametru absent in anul cerut se mosteneste de la ultimul an care l-a
definit. Pentru anii anteriori primei chei se foloseste prima configuratie:
regulile fiscale vechi nu mai sunt suportate.
"""

import json
import os
from functools import lru_cache

from core.settings import BASE_DIR

PARAMETRI_PATH = os.path.join(BASE_DIR, "static", "parametri_fiscali_variabili.json")


def _impara(valori, actualizare):
    """Suprapune recursiv dicturile; scalarii inlocuiesc valoarea veche."""
    rezultat = dict(valori)
    for cheie, valoare in actualizare.items():
        if cheie.startswith("_"):
            continue
        if isinstance(valoare, dict) and isinstance(rezultat.get(cheie), dict):
            rezultat[cheie] = _impara(rezultat[cheie], valoare)
        else:
            rezultat[cheie] = valoare
    return rezultat


@lru_cache(maxsize=1)
def _citeste():
    with open(PARAMETRI_PATH, encoding="utf-8") as fisier:
        return json.load(fisier)


def get_parametri(an: int) -> dict:
    """Parametrii fiscali valabili in anul cerut, cu fallback pe anii anteriori."""
    date = _citeste()
    ani = sorted(int(cheie) for cheie in date if cheie.isdigit())
    aplicabili = [candidat for candidat in ani if candidat <= an]
    if not aplicabili:
        if not ani:
            raise ValueError("Fisierul de parametri fiscali nu contine niciun an.")
        aplicabili = ani[:1]
    rezultat = {}
    for candidat in aplicabili:
        rezultat = _impara(rezultat, date[str(candidat)])
    return rezultat
