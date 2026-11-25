"""Calcul financiar cu ``Decimal`` (precizie de 4 zecimale).

Reguli folosite in toata aplicatia:
- toate calculele intermediate se fac cu ``Decimal`` si se pastreaza cel mult
  4 zecimale (``rotund4``);
- sumele finale (totaluri afisate/platite) se rotunjesc cu ``ROUND_HALF_UP``
  la 2 zecimale (``rotund2``): ce e peste .5 urca, ce e sub .5 coboara;
- conversia din float/str in ``Decimal`` trece intotdeauna prin ``D()``, ca sa
  nu se mosteneasca eroarea de reprezentare a float-ului.
"""

from decimal import ROUND_HALF_UP, Decimal

ZECIMALE_CALCUL = Decimal("0.0001")
ZECIMALE_SUMA = Decimal("0.01")
ZECIMALE_INTREG = Decimal(1)


def D(value) -> Decimal:
    """Convertește o valoare (None, int, float, str, Decimal) în Decimal."""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    # str() evită transformarea lui 0.1 în 0.1000000000000000055...
    return Decimal(str(value))


def rotund4(value) -> Decimal:
    """Valoare folosită în calcule: cel mult 4 zecimale, rotunjire .5 în sus."""
    return D(value).quantize(ZECIMALE_CALCUL, rounding=ROUND_HALF_UP)


def rotund2(value) -> Decimal:
    """Rotunjirea finală a sumelor: >.5 urcă, <.5 coboară (2 zecimale)."""
    return D(value).quantize(ZECIMALE_SUMA, rounding=ROUND_HALF_UP)


def rotund_intreg(value) -> int:
    """Rotunjire la întreg (ex. baza D390), cu .5 în sus."""
    return int(D(value).quantize(ZECIMALE_INTREG, rounding=ROUND_HALF_UP))


def suma(values) -> Decimal:
    """Sumă exactă a unei înșiruiri, fără rotunjiri intermediare."""
    total = Decimal(0)
    for value in values:
        total += D(value)
    return total


def format_suma(value) -> str:
    """Text afișabil pentru o sumă: maxim 2 zecimale, fără zerouri inutile.

    Exemple: ``12.3456 -> "12.35"``, ``100.0000 -> "100"``,
    ``12.30 -> "12.3"``. Se folosește în interfață, PDF-uri și exporturi,
    nu și în calculele intermediare (care rămân la 4 zecimale).
    """
    rotunjit = rotund2(value)
    if not rotunjit:
        return "0"
    return format(rotunjit.normalize(), "f")
