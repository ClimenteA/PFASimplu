"""Regresiune: toate variantele de mijloc fix activeaza campurile de cod."""

import pytest
from helpers import MIJLOC_FIX_CODURI
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_variantele_de_mijloc_fix_activeaza_codurile_de_clasificare(page):
    page.goto("/cheltuieli/")

    # Optiunea obisnuita nu afiseaza campurile de amortizare.
    page.select_option("#id_deductibila", "INTEGRAL")
    expect(page.locator("#amortizare")).to_be_hidden()
    expect(page.locator("#display-coduri-clasificare")).to_be_hidden()

    # Fiecare varianta de mijloc fix le activeaza, ca optiunea initiala.
    for cod in sorted(MIJLOC_FIX_CODURI):
        page.select_option("#id_deductibila", cod)
        expect(page.locator("#amortizare")).to_be_visible()
        expect(page.locator("#display-coduri-clasificare")).to_be_visible()
        expect(page.locator("#id_cod_de_clasificare")).to_be_enabled()
        expect(page.locator("#lista-coduri-de-clasificare li")).not_to_have_count(0)

    # Filtrarea listei dupa cod functioneaza si pe variantele noi.
    page.select_option("#id_deductibila", "MIJLOC_FIX_M1")
    page.fill("#id_cod_de_clasificare", "2.3.")
    expect(page.locator("#lista-coduri-de-clasificare li").first).to_contain_text(
        "2.3."
    )
