import datetime
from functools import cache

import cursvalutarbnr  # noqa: F401  (patch-uit in teste: utils.valuta.cursvalutarbnr)
from cursvalutarbnr import ron_exchange_rate
from django.db import models
from django.utils.translation import gettext_lazy as _

# Cursurile sunt pastrate in tabelul CursBnr si incarcate o singura data;
# functiile isi pastreaza numele si semnatura din versiunea anterioara.
from .cursuri import (  # noqa: F401
    CursBnr,
    curs_bnr_data_exigibilitatii,
    curs_bnr_ziua_bancara_anterioara,
    to_ron,
)
from .decimale import D, rotund2


@cache
def ron_to_eur(amount, year: int):
    january = datetime.date(year, 1, 5).isoformat()
    # Conversia pentru afisare e o suma finala: 2 zecimale, .5 in sus.
    return rotund2(D(amount) / D(ron_exchange_rate(1, "EUR", january)))


class TipTranzactie(models.TextChoices):
    BANCAR = "BANCAR", _("💳 BANCAR")
    NUMERAR = "NUMERAR", _("💵 NUMERAR")


class Valuta(models.TextChoices):
    RON = "RON", _("RON - Romania")
    EUR = "EUR", _("EUR - European Union Zone")
    USD = "USD", _("USD - USA")
    GBP = "GBP", _("GBP - UK")
    CHF = "CHF", _("CHF - Switzerland")
    CAD = "CAD", _("CAD - Canada")
    AED = "AED", _("AED - UAE")
    AUD = "AUD", _("AUD - Australia")
    BGN = "BGN", _("BGN - Bulgaria")
    BRL = "BRL", _("BRL - Brazil")
    CNY = "CNY", _("CNY - China")
    CZK = "CZK", _("CZK - Czech Republic")
    DKK = "DKK", _("DKK - Denmark")
    EGP = "EGP", _("EGP - Egypt")
    HUF = "HUF", _("HUF - Hungary")
    INR = "INR", _("INR - India")
    JPY = "JPY", _("JPY - Japan")
    KRW = "KRW", _("KRW - South Korea")
    MDL = "MDL", _("MDL - Moldova")
    MXN = "MXN", _("MXN - Mexico")
    NOK = "NOK", _("NOK - Norway")
    NZD = "NZD", _("NZD - New Zealand")
    PLN = "PLN", _("PLN - Poland")
    RSD = "RSD", _("RSD - Serbia")
    RUB = "RUB", _("RUB - Russia")
    SEK = "SEK", _("SEK - Sweden")
    THB = "THB", _("THB - Thailand")
    TRY = "TRY", _("TRY - Turkey")
    UAH = "UAH", _("UAH - Ukraine")
    XAU = "XAU", _("XAU - Gold")
    XDR = "XDR", _("XDR - IMF Special Drawing Rights")
    ZAR = "ZAR", _("ZAR - South Africa")
