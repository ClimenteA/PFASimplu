"""Filtre template pentru afișarea sumelor cu cel mult 2 zecimale."""

from django import template

from utils.decimale import format_suma

register = template.Library()


@register.filter
def suma2(value):
    """``12.3456 -> 12.35``, ``100.0000 -> 100`` (fără zerouri inutile)."""
    if value is None or value == "":
        return ""
    return format_suma(value)
