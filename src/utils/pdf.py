"""Generare PDF cu API-ul fluent al pdf_oxide.

Sabloanele HTML ale pdf_oxide nu aseaza corect tabelele si alinierea, asa ca
documentele se deseneaza direct: text, linii si tabele cu pozitii exacte.
"""

import os
import re

from pdf_oxide import DocumentBuilder, EmbeddedFont
from unidecode import unidecode

from core.settings import get_font_path

# A4 in puncti PDF (72 pt = 1 inch).
A4_LATIME = 595.28
A4_INALTIME = 841.89
MARGINE = 56.7
LATIME_UTILA = A4_LATIME - 2 * MARGINE

FONT_NORMAL = "Arial"
FONT_BOLD = "Arial-Bold"

CULOARE_ANTET = (0.93, 0.93, 0.93)
CULOARE_BORDURA = (0.55, 0.55, 0.55)


def _sparge(cuvant: str, latime: float, masoara) -> list[str]:
    """Rupe un cuvant mai lat decat celula, caracter cu caracter."""
    bucati = []
    curent = ""
    for caracter in cuvant:
        if curent and masoara(curent + caracter) > latime:
            bucati.append(curent)
            curent = caracter
        else:
            curent += caracter
    if curent:
        bucati.append(curent)
    return bucati


def _fragmente(cuvant: str, latime: float, masoara) -> list[str]:
    """Rupe un cuvant prea lat, preferand granitele de la `/`."""

    if masoara(cuvant) <= latime:
        return [cuvant]
    fragmente = []
    for parte in re.split(r"(?<=/)", cuvant):
        if masoara(parte) <= latime:
            fragmente.append(parte)
        else:
            fragmente.extend(_sparge(parte, latime, masoara))
    return fragmente


def _rupe(text, latime: float, masoara) -> list[str]:
    """Imparte textul in linii care incap in `latime`, cuvant cu cuvant."""

    linii = []
    for paragraf in unidecode(str(text)).split("\n"):
        cuvinte = paragraf.split()
        if not cuvinte:
            linii.append("")
            continue
        curent = ""
        for cuvant in cuvinte:
            for index, fragment in enumerate(_fragmente(cuvant, latime, masoara)):
                # Fragmentele aceluiasi cuvant se lipesc, dar pot trece pe rand nou.
                candidat = (
                    curent + fragment if index else f"{curent} {fragment}".strip()
                )
                if curent and masoara(candidat) > latime:
                    linii.append(curent)
                    curent = fragment
                else:
                    curent = candidat
        linii.append(curent)
    return linii or [""]


class DocumentPdf:
    """Deseneaza un document A4 cu cursor vertical si paginare automata."""

    def __init__(self):
        self._builder = DocumentBuilder()
        font_dir = get_font_path()
        for nume, fisier in (
            (FONT_NORMAL, "arial.ttf"),
            (FONT_BOLD, "arial-Bold.ttf"),
        ):
            self._builder.register_embedded_font(
                nume, EmbeddedFont.from_file(os.path.join(font_dir, fisier))
            )
        self._pagina = None
        self._pagini = []
        self.y = A4_INALTIME - MARGINE
        self.noua_pagina()

    def noua_pagina(self):
        # Paginile se finalizeaza abia la salvare, ca sa putem scrie subsolul
        # (cu numarul total de pagini) pe fiecare dintre ele.
        if self._pagina is not None:
            self._pagini.append(self._pagina)
        self._pagina = self._builder.a4_page()
        self.font()
        self.y = A4_INALTIME - MARGINE

    def font(self, bold: bool = False, marime: float = 10):
        self._pagina.font(FONT_BOLD if bold else FONT_NORMAL, marime)

    def spatiu(self, puncte: float):
        self.y -= puncte

    def asigura(self, inaltime: float):
        if self.y - inaltime < MARGINE:
            self.noua_pagina()

    def inaltime(self, text, latime: float | None = None, marime: float = 10) -> float:
        """Inaltimea pe care o ocupa un text randat cu `scrie`."""

        latime = LATIME_UTILA if latime is None else latime
        self.font(marime=marime)
        return len(_rupe(text, latime, self._pagina.measure)) * marime * 1.35

    def scrie_la(
        self,
        text,
        x: float = MARGINE,
        latime: float = 0,
        aliniere: str = "left",
        bold: bool = False,
        marime: float = 10,
        y: float | None = None,
    ):
        """Scrie o singura linie la cursorul curent, fara sa il coboare."""

        self.font(bold, marime)
        linie = unidecode(str(text))
        if not linie:
            return
        if aliniere == "right":
            x = x + latime - self._pagina.measure(linie)
        elif aliniere == "center":
            x = x + (latime - self._pagina.measure(linie)) / 2
        self._pagina.at(x, self.y if y is None else y).text(linie)

    def evidentiaza(
        self,
        text,
        bold: bool = True,
        marime: float = 11,
        umplere=CULOARE_ANTET,
        padding: float = 12,
    ):
        """Scrie o linie pe un fond umbrit, aliniata la dreapta."""

        self.font(bold, marime)
        latime = min(
            self._pagina.measure(unidecode(str(text))) + 2 * padding, LATIME_UTILA
        )
        inaltime = marime * 1.9
        self.asigura(inaltime)
        self.y -= inaltime
        x = MARGINE + LATIME_UTILA - latime
        self._pagina.filled_rect(x, self.y, latime, inaltime, *umplere)
        self.scrie_la(
            text,
            x=x,
            latime=latime,
            aliniere="center",
            bold=bold,
            marime=marime,
            y=self.y + (inaltime - marime) / 2 + marime * 0.25,
        )

    def scrie(
        self,
        text,
        x: float = MARGINE,
        latime: float | None = None,
        aliniere: str = "left",
        bold: bool = False,
        marime: float = 10,
    ):
        """Scrie un paragraf (cu rupere pe linii) si coboara cursorul."""

        latime = LATIME_UTILA - (x - MARGINE) if latime is None else latime
        inaltime_rand = marime * 1.35
        self.font(bold, marime)
        for linie in _rupe(text, latime, self._pagina.measure):
            self.asigura(inaltime_rand)
            self.font(bold, marime)
            self.y -= inaltime_rand
            self.scrie_la(linie, x=x, latime=latime, aliniere=aliniere, marime=marime)

    def linie(
        self,
        x1: float = MARGINE,
        x2: float | None = None,
        y: float | None = None,
        grosime: float = 0.5,
        culoare=CULOARE_BORDURA,
    ):
        x2 = A4_LATIME - MARGINE if x2 is None else x2
        y = self.y if y is None else y
        self._pagina.stroke_line(x1, y, x2, y, grosime, culoare)

    def tabel(
        self,
        coloane,
        randuri,
        x: float = MARGINE,
        marime: float = 9,
        marime_antet: float | None = None,
        antet: bool = True,
        umplere_coloana: int | None = None,
    ):
        """Tabel cu bordura, antet umbrit si trecere pe pagina urmatoare.

        `umplere_coloana` umbreste fundalul unei coloane (ex. coloana de
        etichete dintr-un formular), iar `antet=False` deseneaza tabelul fara
        randul de titluri.
        """

        marime_antet = marime if marime_antet is None else marime_antet
        pad_x, pad_y = 4.0, 3.0
        latime_totala = sum(latime for _, latime, _ in coloane)
        dreapta = x + latime_totala

        def bordura(top: float, inaltime: float):
            jos = top - inaltime
            self._pagina.stroke_line(x, jos, dreapta, jos, 0.5, CULOARE_BORDURA)
            self._pagina.stroke_line(x, top, dreapta, top, 0.5, CULOARE_BORDURA)
            cx = x
            for _, latime, _ in coloane:
                self._pagina.stroke_line(cx, top, cx, jos, 0.5, CULOARE_BORDURA)
                cx += latime
            self._pagina.stroke_line(dreapta, top, dreapta, jos, 0.5, CULOARE_BORDURA)

        def umple(coloana: int, top: float, inaltime: float):
            cx = x
            for index, (_, latime, _) in enumerate(coloane):
                if index == coloana:
                    self._pagina.filled_rect(
                        cx, top - inaltime, latime, inaltime, *CULOARE_ANTET
                    )
                    return
                cx += latime

        def celule(valori, top: float, bold: bool, marime: float):
            inaltime_rand = marime * 1.3
            self.font(bold, marime)
            continut = [
                _rupe(valoare, latime - 2 * pad_x, self._pagina.measure)
                for valoare, (_, latime, _) in zip(valori, coloane)
            ]
            self.font(bold, marime)
            cx = x
            for linii, (_, latime, aliniere) in zip(continut, coloane):
                cy = top - pad_y - marime * 0.95
                for linie in linii:
                    if linie:
                        if aliniere == "right":
                            lx = cx + latime - pad_x - self._pagina.measure(linie)
                        elif aliniere == "center":
                            lx = cx + (latime - self._pagina.measure(linie)) / 2
                        else:
                            lx = cx + pad_x
                        self._pagina.at(lx, cy).text(linie)
                    cy -= inaltime_rand
                cx += latime

        def rand(valori, bold: bool = False, umplere=None, marime=marime) -> float:
            inaltime_rand = marime * 1.3
            self.font(bold, marime)
            nr_linii = max(
                len(_rupe(valoare, latime - 2 * pad_x, self._pagina.measure))
                for valoare, (_, latime, _) in zip(valori, coloane)
            )
            inaltime = nr_linii * inaltime_rand + 2 * pad_y
            if self.y - inaltime < MARGINE:
                self.noua_pagina()
                if antet:
                    rand(titluri, bold=True, umplere=CULOARE_ANTET, marime=marime_antet)
            top = self.y
            if umplere:
                self._pagina.filled_rect(
                    x, top - inaltime, latime_totala, inaltime, *umplere
                )
            elif umplere_coloana is not None:
                umple(umplere_coloana, top, inaltime)
            celule(valori, top, bold, marime)
            bordura(top, inaltime)
            self.y = top - inaltime
            return inaltime

        titluri = [titlu for titlu, _, _ in coloane]
        if antet:
            rand(titluri, bold=True, umplere=CULOARE_ANTET, marime=marime_antet)
        for valori in randuri:
            rand(valori)

    def salveaza(self, cale: str, subsol: str | None = None) -> str:
        """Finalizeaza paginile, scrie subsolul pe fiecare si salveaza PDF-ul.

        `subsol` poate contine `{pagina}` si `{total}`.
        """

        pagini = [*self._pagini, self._pagina]
        for numar, pagina in enumerate(pagini, start=1):
            self._pagina = pagina
            if subsol:
                pagina.stroke_line(
                    MARGINE,
                    MARGINE - 14,
                    A4_LATIME - MARGINE,
                    MARGINE - 14,
                    0.5,
                    CULOARE_BORDURA,
                )
                self.y = MARGINE - 24
                self.scrie_la(
                    subsol.format(pagina=numar, total=len(pagini)),
                    latime=LATIME_UTILA,
                    aliniere="center",
                    marime=8,
                )
            pagina.done()
        self._builder.save(cale)
        return cale
