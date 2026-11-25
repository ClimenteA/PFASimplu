"""Cursuri BNR pastrate in baza de date, o singura data per (data, valuta).

Inainte valorile erau recalculate la fiecare salvare si pastrate in coloane
derivate (`suma_in_ron`, `curs_bnr_aplicat`, ...), iar rapoartele vechi puteau
obtine cursuri diferite intre doua rulari. Aici cursul este un fapt stocat,
incarcat lazy din `cursvalutarbnr` si refolosit de toate calculele.
"""

import datetime

import cursvalutarbnr
from django.db import models

from .decimale import D, rotund4


class CursBnr(models.Model):
    data = models.DateField()
    valuta = models.CharField(max_length=3)
    curs = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        app_label = "utils"
        constraints = [
            models.UniqueConstraint(
                fields=["data", "valuta"], name="unic_curs_bnr_data_valuta"
            )
        ]

    def __str__(self):
        return f"{self.data.isoformat()} {self.valuta} {self.curs}"


def _data(value) -> datetime.date:
    if isinstance(value, str):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    if isinstance(value, datetime.datetime):
        return value.date()
    return value or datetime.date.today()


def _curs_din_bnr(currency: str, zi: datetime.date):
    """Cursul publicat de BNR in ziua `zi` (sau ultima zi disponibila <= zi)."""
    rates = cursvalutarbnr.get_bnr_rates(zi)
    zile = [
        datetime.date.fromisoformat(d)
        for d in rates
        if datetime.date.fromisoformat(d) <= zi
    ]
    if not zile:
        raise ValueError(f"Nu exista curs BNR publicat pana la {zi.isoformat()}")
    ultima_zi = max(zile)
    curs = rotund4(D(rates[ultima_zi.isoformat()][currency]))
    # Salvam tot ce am obtinut pentru ziua gasita, casa nu mai intervenim la
    # urmatoarea operatiune din aceeasi zi (weekend/sarbatoare inclusiv).
    for valuta, valoare in rates[ultima_zi.isoformat()].items():
        CursBnr.objects.get_or_create(
            data=ultima_zi,
            valuta=valuta,
            defaults={"curs": rotund4(D(valoare))},
        )
    return curs


def _curs_stocat(currency: str, zi: datetime.date):
    stored = CursBnr.objects.filter(data=zi, valuta=currency).first()
    return D(stored.curs) if stored else None


def curs_bnr_ziua_bancara_anterioara(currency: str, dateValue):
    """Cursul din ultima zi bancara *strict inainte* de operatiune."""
    if currency == "RON":
        return D("1")
    zi = _data(dateValue)
    # Cautam in ultimele 7 zile; daca nu gasim, intrebam BNR o data.
    for delta in range(1, 8):
        curs = _curs_stocat(currency, zi - datetime.timedelta(days=delta))
        if curs is not None:
            return curs
    rates = cursvalutarbnr.get_bnr_rates(zi)
    zile = [
        datetime.date.fromisoformat(d)
        for d in rates
        if datetime.date.fromisoformat(d) < zi
    ]
    if not zile:
        raise ValueError(f"Nu exista curs BNR publicat inainte de {zi.isoformat()}")
    ultima_zi = max(zile)
    for valuta, valoare in rates[ultima_zi.isoformat()].items():
        CursBnr.objects.get_or_create(
            data=ultima_zi,
            valuta=valuta,
            defaults={"curs": rotund4(D(valoare))},
        )
    return rotund4(D(rates[ultima_zi.isoformat()][currency]))


def curs_bnr_data_exigibilitatii(currency: str, dateValue):
    """Cursul valabil la data exigibilitatii (art. 290 alin. (2) Cod fiscal)."""
    if currency == "RON":
        return D("1")
    zi = _data(dateValue)
    curs = _curs_stocat(currency, zi)
    if curs is not None:
        return curs
    return _curs_din_bnr(currency, zi)


def to_ron(amount, currency: str, dateValue=None):
    if not dateValue:
        dateValue = datetime.date.today()
    rate = curs_bnr_ziua_bancara_anterioara(currency, _data(dateValue))
    return rotund4(D(amount) * D(rate))
