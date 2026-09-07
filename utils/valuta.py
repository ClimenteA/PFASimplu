import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
import cursvalutarbnr
from cursvalutarbnr import ron_exchange_rate
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache


def curs_bnr_ziua_bancara_anterioara(currency: str, dateValue: datetime.date) -> float:
    """Cursul BNR cerut de OMFP 170/2015 pct. 18 pentru o operatiune din ziua dateValue:
    "cursul de schimb al pietei valutare, comunicat de BNR, din ultima zi bancara
    anterioara operatiunii, disponibil ca informatie la momentul efectuarii operatiunii".
    Se ia ultimul curs publicat de BNR STRICT inainte de data operatiunii (pentru luni
    cursul de vineri, pentru o zi de dupa o sarbatoare cursul din ultima zi lucratoare)."""
    if currency == "RON":
        return 1.0
    rates = cursvalutarbnr.get_bnr_rates(dateValue)
    zile_anterioare = [
        datetime.date.fromisoformat(d) for d in rates.keys()
        if datetime.date.fromisoformat(d) < dateValue
    ]
    if not zile_anterioare:
        raise ValueError(f"Nu exista curs BNR publicat inainte de {dateValue.isoformat()}")
    ultima_zi = max(zile_anterioare)
    return float(rates[ultima_zi.isoformat()][currency])


@lru_cache(maxsize=None)
def to_ron(amount: float, currency: str, dateValue: datetime.date):
    if isinstance(dateValue, str):
        dateValue = datetime.datetime.strptime(dateValue, "%Y-%m-%d").date()
    if not dateValue:
        dateValue = datetime.date.today()
    rate = curs_bnr_ziua_bancara_anterioara(currency, dateValue)
    result = (Decimal(str(amount)) * Decimal(str(rate))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return float(result)


@lru_cache(maxsize=None)
def ron_to_eur(amount: float, year: int):
    january = datetime.date(year, 1, 5).isoformat()
    return round(
        (amount / ron_exchange_rate(1, "EUR", january)),
        2,
    )


class TipTranzactie(models.TextChoices):
    BANCAR = "BANCAR", _("💳 BANCAR")
    NUMERAR = "NUMERAR", _("💵 NUMERAR")


class Valuta(models.TextChoices):
    RON = "RON", _('RON - Romania')
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