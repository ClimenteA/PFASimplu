import itertools
import logging
import os
from copy import copy

import matplotlib
import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from cheltuieli.calcul import (
    calculeaza_deduceri_anului,
    q_inventar,
    q_mijloc_fix,
    q_scos_din_uz,
)
from cheltuieli.models import CheltuialaModel, Deductibilitate
from core.settings import get_media_path
from documente.models import DocumenteModel
from incasari.models import IncasariModel, SursaVenit
from setari.models import SetariModel
from utils.calcule import calculeaza_taxe_si_impozite
from utils.decimale import D, format_suma, rotund2
from utils.tva import calculeaza_jurnal_cumparari
from utils.valuta import ron_to_eur
from utils.views import download_csv_or_xlsx, download_dataframe

# SVG inseamna ca graficele nu au nevoie de backend GUI.
matplotlib.use("SVG")

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def in_valuta_afisare(value, valuta: str, anul: int):
    """Valoarea afisata/exportata in moneda selectata, cu 2 zecimale."""
    valoare = D(value)
    if valuta == "EUR":
        return ron_to_eur(valoare, anul)
    return rotund2(valoare)


def get_valuta_from_request(request) -> str:
    return request.GET.get("valuta") or "RON"


def registru_jurnal_dataframe(data):
    """DataFrame-ul Registrului Jurnal (incasari si plati), cu antetul afisat."""
    df = pd.DataFrame(data)
    df = df.drop(columns=["end_of_month", "documentId"])
    return df.rename(
        columns={
            "nr_crt": "Nr.Crt.",
            "data": "Data",
            "documentul": "Documentul (fel, numar)",
            "felul_operatiunii": "Felul operatiunii (explicatii)",
            "incasari_numerar": "Incasari Numerar",
            "incasari_banca": "Incasari Banca",
            "plati_numerar": "Plati Numerar",
            "plati_banca": "Plati Banca",
        }
    )


def registru_fiscal_dataframe(data):
    """DataFrame-ul Registrului de evidenta fiscala, cu antetul afisat."""
    df = pd.DataFrame(data)
    return df.rename(
        columns={
            "nr_crt": "Nr.Crt.",
            "elemente_de_calcul": "Elemente de calcul pentru stabilirea venitului net annual/pierderii nete anuale",
            "valoare": "Valoare",
            "anul": "Anul",
        }
    )


def registru_inventar_dataframe(data):
    """DataFrame-ul Registrului-inventar, cu antetul afisat.
    `data` vine din get_registru_inventar(dbid=True)."""
    df = pd.DataFrame(data)
    df = df.drop(columns=["mijloc_fix", "db_id"])
    return df.rename(
        columns={
            "nr_crt": "Nr.Crt.",
            "nume_cheltuiala": "Denumirea elementelor inventariate",
            "deducere_in_ron": "Valoare inventar",
            "data_inserarii": "Data",
            "fisier": "Document",
        }
    )


def jurnal_cumparari_dataframe(jurnal):
    """DataFrame-ul Jurnalului pentru cumparari (taxare inversa), cu antetul afisat."""
    df = pd.DataFrame(jurnal["randuri"])
    return df.rename(
        columns={
            "nr_crt": "Nr.Crt.",
            "data_doc": "Document Data",
            "nr_doc": "Document Numar",
            "furnizor_denumire": "Furnizor Denumire",
            "furnizor_cod_fiscal": "Furnizor Cod Fiscal",
            "total_document": "Total document (inclusiv TVA)",
            "baza": "Baza impozitare",
            "tva": "Valoare T.V.A.",
            "cod_referinta": "Referinta cod",
            "fisier": "Document justificativ (fisier)",
        }
    )


class RegistruJurnalDescarcaView(View):
    def get(self, request):
        anul = get_year_from_request(request)
        incasari, cheltuieli = incasari_cheltuieli_dupa_anul_inserarii(anul)
        data = get_registru_jurnal_incasari_si_plati(
            request,
            incasari,
            cheltuieli,
            valuta=get_valuta_from_request(request),
        )

        if not data:
            return redirect("/registre/")

        df = registru_jurnal_dataframe(data)
        return download_dataframe(request, df, "registru_jurnal_incasari_si_plati")


class RegistruFiscalDescarcaView(View):
    def get(self, request):
        overview_data = get_cards_and_charts_data(request)
        data = get_registru_de_evidenta_fiscala(
            request,
            overview_data["total_incasari_brut"],
            overview_data["total_incasari_net"],
            overview_data["total_cheltuieli"],
            valuta=overview_data["valuta"],
        )
        df = registru_fiscal_dataframe(data)

        return download_csv_or_xlsx(request, df, "registrul_de_evidenta_fiscala")


class RegistruInventarDescarcaView(View):
    def get(self, request):
        data = get_registru_inventar(
            dbid=True,
            valuta=get_valuta_from_request(request),
            anul=get_year_from_request(request),
        )
        if not data:
            messages.add_message(
                request,
                messages.ERROR,
                "Registrul-inventar este gol, nu exista nimic de exportat.",
                extra_tags="🟥 Eroare!",
            )
            return redirect("/registre/")

        # Doar numele documentului ajunge in export; fisierele nu sunt citite
        # sau copiate, deci documentele lipsa de pe disc nu blocheaza descarcarea.
        for item in data:
            item["fisier"] = os.path.basename(item["fisier"])

        df = registru_inventar_dataframe(data)
        return download_dataframe(request, df, "registru_inventar")


class RegistruJurnalCumparariDescarcaView(View):
    """Jurnalul pentru cumparari (TVA taxare inversa): CSV sau XLSX,
    pe luna (daca se da parametrul luna) sau pe tot anul."""

    def get(self, request):
        anul = get_year_from_request(request)
        luna = request.GET.get("luna")
        luna = int(luna) if luna else None
        valuta = get_valuta_from_request(request)

        jurnal = calculeaza_jurnal_cumparari(anul, luna)
        if not jurnal:
            messages.add_message(
                request,
                messages.ERROR,
                "Jurnalul de cumparari este gol: nu exista cheltuieli cu taxare inversa (UE/non-UE).",
                extra_tags="🟥 Eroare!",
            )
            return redirect("/registre/")

        perioada = f"{anul}_{luna:02d}" if luna else str(anul)
        if valuta == "EUR":
            for rand in jurnal["randuri"]:
                for camp in ("total_document", "baza", "tva"):
                    rand[camp] = in_valuta_afisare(rand[camp], valuta, anul)

        df = jurnal_cumparari_dataframe(jurnal)
        return download_dataframe(request, df, f"jurnal_cumparari_{perioada}")


class RegistreView(View):
    def get(self, request):
        overview_data = get_cards_and_charts_data(request)
        valuta = overview_data["valuta"]
        anul = overview_data["anul"]
        registru_fiscal = get_registru_de_evidenta_fiscala(
            request,
            overview_data["total_incasari_brut"],
            overview_data["total_incasari_net"],
            overview_data["total_cheltuieli"],
            valuta=valuta,
        )
        registru_jurnal_incasari_si_plati = get_registru_jurnal_incasari_si_plati(
            request, valuta=valuta, anul=anul
        )
        registru_inventar = get_registru_inventar(valuta=valuta, anul=anul)
        jurnal_cumparari = calculeaza_jurnal_cumparari(anul)
        if jurnal_cumparari and valuta == "EUR":
            for rand in jurnal_cumparari["randuri"]:
                for camp in ("total_document", "baza", "tva"):
                    rand[camp] = in_valuta_afisare(rand[camp], valuta, anul)

        return render(
            request,
            "registre.html",
            context={
                **overview_data,
                "rjip": registru_jurnal_incasari_si_plati,
                "ref": registru_fiscal,
                "ri": registru_inventar,
                "rjc": jurnal_cumparari,
            },
        )


def get_obiecte_inventar():
    # Campurile derivate nu mai sunt coloane: folosim Q-urile din calcul.py.
    # `q_scos_din_uz()` selecteaza exact obiectele care AU data iesirii din uz,
    # deci negarea lor corespunde vechiului `scos_din_uz=False`.
    results = CheltuialaModel.objects.filter(q_inventar() & ~q_scos_din_uz()).order_by(
        "data_inserarii"
    )

    return results


def get_registru_inventar(
    dbid: bool = True,
    obiecte_inventar=None,
    valuta: str = "RON",
    anul: int | None = None,
):

    if obiecte_inventar is None:
        obiecte_inventar = get_obiecte_inventar()

    anul = anul or timezone.now().year
    idx = 1
    rows = []
    for item in obiecte_inventar:
        data = {
            "nr_crt": idx,
            "nume_cheltuiala": item.nume_cheltuiala,
            "deducere_in_ron": in_valuta_afisare(item.deducere_in_ron, valuta, anul),
            "data_inserarii": item.data_inserarii.isoformat(),
            "fisier": item.fisier.path,
            "mijloc_fix": item.mijloc_fix,
        }

        if dbid:
            data.update({"db_id": item.id})

        rows.append(data)
        idx += 1

    return rows


def get_incasari_pe_surse(anul: int, valuta: str = "RON"):
    # `suma_in_ron` nu mai e stocata: se calculeaza din suma/valuta/data.
    # Luam in calcul doar incasarile efectiv incasate in anul cerut, pentru ca
    # breakdown-ul pe surse sa se adune la `IncasariModel.get_total_incasari(anul)`.
    totaluri = {sursa.value: D(0) for sursa in SursaVenit}
    for incasare in IncasariModel.objects.filter(
        data_incasarii__year=anul, data_incasarii__isnull=False
    ):
        if incasare.sursa_venit in totaluri:
            totaluri[incasare.sursa_venit] += D(incasare.suma_in_ron)

    incasari_pe_surse_de_venit = []
    for sursa in SursaVenit:
        valoare = totaluri[sursa.value]
        if valoare:
            incasari_pe_surse_de_venit.append(
                {
                    "nume": str(sursa.label),
                    "valoare": in_valuta_afisare(valoare, valuta, anul),
                }
            )

    return incasari_pe_surse_de_venit


def get_cheltuieli_pe_deductibilitate(anul: int, valuta: str = "RON"):
    # Registrul fiscal arata sumele DEDUSE (deducere_in_ron), nu sumele platite, ca liniile
    # sa se adune la "Total cheltuieli" (care e calculat tot pe deducere_in_ron).
    # Deducerile (cu plafonarile anuale) se calculeaza o singura data pe an.
    deduceri = calculeaza_deduceri_anului(anul)

    # Ordinea de afisare ramane aceeasi; `None` marcheaza pozitia amortizarilor,
    # care se calculeaza lunar, pe toate mijloacele fixe active in an.
    categorii = [
        Deductibilitate.DEDUCTIBILA_INTEGRAL,
        Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR,
        Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII,
        None,
        Deductibilitate.DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI,
        Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE,
        Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024,
        Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3,
        Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_OCUPATIONALA,
        Deductibilitate.DEDUCTIBILA_PARTIAL_PEPP,
        Deductibilitate.DEDUCTIBILA_PARTIAL_ETF,
        Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT,
        Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL,
        Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE,
        Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG,
        Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG,
    ]
    totaluri = {cod.value: D(0) for cod in categorii if cod is not None}

    for cheltuiala in CheltuialaModel.objects.filter(data_inserarii__year=anul):
        if cheltuiala.deductibila in totaluri:
            totaluri[cheltuiala.deductibila] += D(deduceri.get(cheltuiala.pk) or 0)

    cheltuieli_d_integral_amortizari = D(0)
    for amortizare in CheltuialaModel.objects.filter(q_mijloc_fix()):
        luni = amortizare.luni_amortizare_in_an(anul)
        lunar = amortizare.amortizare_lunara
        if luni and lunar is not None:
            cheltuieli_d_integral_amortizari += D(luni) * D(lunar)

    cheltuieli_pe_deductibilitate = []
    for cod in categorii:
        if cod is None:
            if cheltuieli_d_integral_amortizari:
                cheltuieli_pe_deductibilitate.append(
                    {
                        "nume": str(
                            Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.label
                        ),
                        "valoare": in_valuta_afisare(
                            cheltuieli_d_integral_amortizari, valuta, anul
                        ),
                    }
                )
            continue

        valoare = totaluri[cod.value]
        if valoare:
            cheltuieli_pe_deductibilitate.append(
                {
                    "nume": str(cod.label),
                    "valoare": in_valuta_afisare(valoare, valuta, anul),
                }
            )

    return cheltuieli_pe_deductibilitate


def get_registru_de_evidenta_fiscala(
    request,
    total_incasari_brut,
    total_incasari_net,
    total_cheltuieli,
    anul=None,
    valuta=None,
):
    # `anul` poate fi dat explicit (ex. exportul pe an din Setari);
    # altfel se ia din query params, cu fallback pe anul curent.
    if anul is None:
        anul = request.GET.get("anul")
        anul = int(anul) if anul else timezone.now().year
    if valuta is None:
        valuta = get_valuta_from_request(request)

    incasari_pe_surse_de_venit = get_incasari_pe_surse(anul, valuta)
    cheltuieli_pe_deductibilitate = get_cheltuieli_pe_deductibilitate(anul, valuta)

    rows = [
        {
            "nr_crt": 1,
            "elemente_de_calcul": "Total incasari brut:",
            "valoare": total_incasari_brut,
            "anul": anul,
        }
    ]

    idx = None

    if len(incasari_pe_surse_de_venit) > 0:
        for idx, item in enumerate(incasari_pe_surse_de_venit, start=2):
            rows.append(
                {
                    "nr_crt": idx,
                    "elemente_de_calcul": item["nume"],
                    "valoare": item["valoare"],
                    "anul": anul,
                }
            )
        idx += 1

    idx = idx or 2
    rows.append(
        {
            "nr_crt": idx,
            "elemente_de_calcul": "Total cheltuieli:",
            "valoare": total_cheltuieli,
            "anul": anul,
        }
    )

    if len(cheltuieli_pe_deductibilitate) > 0:
        idx += 1
        for idx, item in enumerate(cheltuieli_pe_deductibilitate, start=idx):
            rows.append(
                {
                    "nr_crt": idx,
                    "elemente_de_calcul": item["nume"],
                    "valoare": item["valoare"],
                    "anul": anul,
                }
            )

    idx += 1
    rows.append(
        {
            "nr_crt": idx,
            "elemente_de_calcul": "Venit net realizat:",
            "valoare": total_incasari_net,
            "anul": anul,
        }
    )

    return rows


LUNI_RO = {
    1: "Ianuarie",
    2: "Februarie",
    3: "Martie",
    4: "Aprilie",
    5: "Mai",
    6: "Iunie",
    7: "Iulie",
    8: "August",
    9: "Septembrie",
    10: "Octombrie",
    11: "Noiembrie",
    12: "Decembrie",
}


def get_year_from_request(request):
    anul = request.GET.get("anul")
    anul = int(anul) if anul else timezone.now().year
    return anul


def incasari_cheltuieli_dupa_anul_inserarii(anul: int):
    # O incasare conteaza la anul in care banii au intrat in cont;
    # cheltuiala ramane la anul inserarii.
    incasari = IncasariModel.objects.filter(
        data_incasarii__year=anul, data_incasarii__isnull=False
    )
    cheltuieli = CheltuialaModel.objects.filter(data_inserarii__year=anul)
    return incasari, cheltuieli


def get_registru_jurnal_incasari_si_plati(
    request, incasari=None, cheltuieli=None, anul=None, valuta=None
):
    # `anul` poate fi dat explicit (ex. exportul pe an din Setari).
    if anul is None:
        anul = get_year_from_request(request)
    if valuta is None:
        valuta = get_valuta_from_request(request)

    if incasari is None and cheltuieli is None:
        incasari, cheltuieli = incasari_cheltuieli_dupa_anul_inserarii(anul)

    combined_data = sorted(
        itertools.chain(incasari, cheltuieli), key=lambda x: x.data_inserarii
    )

    result = []
    total_incasari_numerar = D(0)
    total_incasari_bancar = D(0)
    total_cheltuieli_numerar = D(0)
    total_cheltuieli_bancar = D(0)
    prev_month = None
    for idx, entry in enumerate(combined_data, start=1):
        current_month = entry.data_inserarii.month

        if prev_month is not None and current_month != prev_month:
            result.append(
                {
                    "nr_crt": "-",
                    "data": "-",
                    "documentul": "-",
                    "documentId": None,
                    "felul_operatiunii": f"Calcul total luna {LUNI_RO[prev_month]}",
                    "incasari_numerar": rotund2(total_incasari_numerar),
                    "incasari_banca": rotund2(total_incasari_bancar),
                    "plati_numerar": rotund2(total_cheltuieli_numerar),
                    "plati_banca": rotund2(total_cheltuieli_bancar),
                    "end_of_month": True,
                }
            )
            total_incasari_numerar = D(0)
            total_incasari_bancar = D(0)
            total_cheltuieli_numerar = D(0)
            total_cheltuieli_bancar = D(0)

        prev_month = current_month

        if isinstance(entry, IncasariModel):
            incasari_numerar = (
                in_valuta_afisare(entry.suma_in_ron, valuta, anul)
                if entry.tip_tranzactie == "NUMERAR"
                else D(0)
            )
            incasari_bancar = (
                in_valuta_afisare(entry.suma_in_ron, valuta, anul)
                if entry.tip_tranzactie == "BANCAR"
                else D(0)
            )

            total_incasari_numerar += incasari_numerar
            total_incasari_bancar += incasari_bancar

            result.append(
                {
                    "nr_crt": idx,
                    "data": entry.data_inserarii.isoformat(),
                    "documentul": entry.fisier,
                    "documentId": str(entry.fisier).split("_")[0],
                    "felul_operatiunii": "Incasare"
                    + (
                        f" ({format_suma(entry.suma)} {entry.valuta})"
                        if entry.valuta != "RON"
                        else ""
                    ),
                    "incasari_numerar": incasari_numerar,
                    "incasari_banca": incasari_bancar,
                    "plati_numerar": D(0),
                    "plati_banca": D(0),
                    "end_of_month": False,
                }
            )

        else:
            cheltuieli_numerar = (
                in_valuta_afisare(entry.suma_in_ron, valuta, anul)
                if entry.tip_tranzactie == "NUMERAR"
                else D(0)
            )
            cheltuieli_bancar = (
                in_valuta_afisare(entry.suma_in_ron, valuta, anul)
                if entry.tip_tranzactie == "BANCAR"
                else D(0)
            )

            total_cheltuieli_numerar += cheltuieli_numerar
            total_cheltuieli_bancar += cheltuieli_bancar

            result.append(
                {
                    "nr_crt": idx,
                    "data": entry.data_inserarii.isoformat(),
                    "documentul": entry.fisier,
                    "documentId": str(entry.fisier).split("_")[0],
                    "felul_operatiunii": f"Cheltuiala {entry.nume_cheltuiala}"
                    + (
                        f" ({format_suma(entry.suma)} {entry.valuta})"
                        if entry.valuta != "RON"
                        else ""
                    ),
                    "incasari_numerar": D(0),
                    "incasari_banca": D(0),
                    "plati_numerar": cheltuieli_numerar,
                    "plati_banca": cheltuieli_bancar,
                    "end_of_month": False,
                }
            )

    if prev_month is not None:
        result.append(
            {
                "nr_crt": "-",
                "data": "-",
                "documentul": "-",
                "documentId": None,
                "felul_operatiunii": f"Calcul total luna {LUNI_RO[prev_month]}",
                "incasari_numerar": rotund2(total_incasari_numerar),
                "incasari_banca": rotund2(total_incasari_bancar),
                "plati_numerar": rotund2(total_cheltuieli_numerar),
                "plati_banca": rotund2(total_cheltuieli_bancar),
                "end_of_month": True,
            }
        )

    return result


def get_cards_and_charts_data(request):

    current_year = timezone.now().year
    anul = request.GET.get("anul")
    valuta = request.GET.get("valuta") or "RON"
    in_euro = valuta == "EUR"
    anul = int(anul) if anul else current_year

    furnizor = SetariModel.objects.first()

    # CALCUL INCASARI, CHELTUIELI
    try:
        total_neincasate = IncasariModel.get_total_neincasate(anul)
        total_incasari_brut = IncasariModel.get_total_incasari(anul)
        try:
            total_cheltuieli = CheltuialaModel.get_total_cheltuieli(anul)
        except Exception as err:
            logger.warning(
                "Nu s-a putut calcula totalul cheltuielilor pentru anul %s; "
                "folosesc 0: %s",
                anul,
                err,
            )
            total_cheltuieli = 0

        # Venitul net poate fi negativ (pierdere fiscala); se afiseaza ca atare in registrul
        # fiscal, iar taxele se calculeaza pe baza pozitiva.
        total_incasari_net = rotund2(D(total_incasari_brut) - D(total_cheltuieli))

        cheltuieli = CheltuialaModel.objects.all()
        if cheltuieli:
            c_newest_date = cheltuieli.latest("data_inserarii")
            c_oldest_date = cheltuieli.earliest("data_inserarii")

        incasari = IncasariModel.objects.all()
        if incasari:
            i_newest_date = incasari.latest("data_inserarii")
            i_oldest_date = incasari.earliest("data_inserarii")

        if cheltuieli and incasari:
            years_list = [
                c_newest_date.data_inserarii.year,
                i_newest_date.data_inserarii.year,
                c_oldest_date.data_inserarii.year,
                i_oldest_date.data_inserarii.year,
                current_year,
            ]
        elif cheltuieli:
            years_list = [
                c_newest_date.data_inserarii.year,
                c_oldest_date.data_inserarii.year,
                current_year,
            ]
        elif incasari:
            years_list = [
                i_newest_date.data_inserarii.year,
                i_oldest_date.data_inserarii.year,
                current_year,
            ]
        else:
            years_list = [current_year]

        ani_inregistrati = reversed(range(min(years_list), max(years_list) + 1))

        incasari_pe_luni = IncasariModel.get_total_incasari_pe_luni(anul)
        cheltuieli_pe_luni = CheltuialaModel.get_total_cheltuieli_pe_luni(anul)

        media_url_chart_incasari_cheltuieli = create_bar_plot(
            anul, incasari_pe_luni, cheltuieli_pe_luni, valuta
        )

    except Exception:
        logger.exception(
            "Eroare la calculul cardurilor/graficelor pentru anul %s; "
            "folosesc valori zero",
            anul,
        )
        total_neincasate = 0
        total_incasari_brut = 0
        total_incasari_net = 0
        total_cheltuieli = 0
        ani_inregistrati = [anul]
        media_url_chart_incasari_cheltuieli = create_bar_plot(
            anul, [0] * 12, [0] * 12, valuta
        )

    # CALCUL TAXE IMPOZITE

    alte_venituri_an = IncasariModel.get_total_incasari_alte_surse(anul)
    if furnizor:
        la_stat = calculeaza_taxe_si_impozite(
            max(total_incasari_net, 0),
            anul,
            furnizor.scutit_cas,
            furnizor.scutit_cass,
            furnizor.scutit_impozit,
            alte_venituri=alte_venituri_an,
        )
    else:
        la_stat = calculeaza_taxe_si_impozite(
            max(total_incasari_net, 0),
            anul,
            alte_venituri=alte_venituri_an,
        )

    total_platite_la_stat_pe_toti_anii = DocumenteModel.total_plati_la_stat()

    years = copy(ani_inregistrati)
    total_incasari_net_pe_toti_anii = D(0)
    total_incasari_brut_pe_toti_anii = D(0)
    total_cheltuieli_pe_toti_anii = D(0)
    total_de_platit_la_stat_pe_toti_anii = D(0)
    for yr in years:
        tib = IncasariModel.get_total_incasari(yr)
        tc = CheltuialaModel.get_total_cheltuieli(yr)
        total_cheltuieli_pe_toti_anii += D(tc)
        total_incasari_brut_pe_toti_anii += D(tib)
        incasari_net = rotund2(D(tib) - D(tc))

        alte_venituri_yr = IncasariModel.get_total_incasari_alte_surse(yr)
        if furnizor:
            tiy = calculeaza_taxe_si_impozite(
                max(incasari_net, 0),
                yr,
                furnizor.scutit_cas,
                furnizor.scutit_cass,
                furnizor.scutit_impozit,
                alte_venituri=alte_venituri_yr,
            )["total_taxe_impozite"]
        else:
            tiy = calculeaza_taxe_si_impozite(
                max(incasari_net, 0),
                yr,
                alte_venituri=alte_venituri_yr,
            )["total_taxe_impozite"]

        total_de_platit_la_stat_pe_toti_anii += D(tiy)

    total_incasari_net_pe_toti_anii = (
        total_incasari_brut_pe_toti_anii
        - total_cheltuieli_pe_toti_anii
        - total_de_platit_la_stat_pe_toti_anii
    )

    total_incasari_net_pe_toti_anii = max(0, total_incasari_net_pe_toti_anii)

    total_incasari_net_pe_toti_anii = rotund2(total_incasari_net_pe_toti_anii)

    # Pozitiv = mai e de platit; negativ = platit in plus fata de estimare.
    rest_de_plata_catre_stat = rotund2(
        D(total_de_platit_la_stat_pe_toti_anii) - D(total_platite_la_stat_pe_toti_anii)
    )

    return {
        "anul": anul,
        "valuta": valuta,
        "ani_inregistrati": ani_inregistrati,
        "media_url_chart_incasari_cheltuieli": media_url_chart_incasari_cheltuieli,
        "rest_de_plata_catre_stat": (
            ron_to_eur(rest_de_plata_catre_stat, anul)
            if in_euro
            else rest_de_plata_catre_stat
        ),
        "total_platite_la_stat_pe_toti_anii": (
            ron_to_eur(total_platite_la_stat_pe_toti_anii, anul)
            if in_euro
            else total_platite_la_stat_pe_toti_anii
        ),
        "total_incasari_net_pe_toti_anii": (
            ron_to_eur(total_incasari_net_pe_toti_anii, anul)
            if in_euro
            else total_incasari_net_pe_toti_anii
        ),
        "total_neincasate": (
            ron_to_eur(total_neincasate, anul) if in_euro else total_neincasate
        ),
        "total_incasari_brut": (
            ron_to_eur(total_incasari_brut, anul) if in_euro else total_incasari_brut
        ),
        "total_incasari_net": (
            ron_to_eur(total_incasari_net, anul) if in_euro else total_incasari_net
        ),
        "total_cheltuieli": (
            ron_to_eur(total_cheltuieli, anul) if in_euro else total_cheltuieli
        ),
        "total_taxe_impozite": (
            ron_to_eur(la_stat["total_taxe_impozite"], anul)
            if in_euro
            else la_stat["total_taxe_impozite"]
        ),
        "cas_pensie": (
            ron_to_eur(la_stat["cas_pensie"], anul)
            if in_euro
            else la_stat["cas_pensie"]
        ),
        "cass_sanatate": (
            ron_to_eur(la_stat["cass_sanatate"], anul)
            if in_euro
            else la_stat["cass_sanatate"]
        ),
        "impozit_pe_venit": (
            ron_to_eur(la_stat["impozit_pe_venit"], anul)
            if in_euro
            else la_stat["impozit_pe_venit"]
        ),
    }


def create_bar_plot(
    anul: int,
    incasari_pe_luni: list[float],
    cheltuieli_pe_luni: list[float],
    currency: str = "RON",
):

    if currency == "EUR":
        incasari_pe_luni = [ron_to_eur(i, anul) for i in incasari_pe_luni]
        cheltuieli_pe_luni = [ron_to_eur(c, anul) for c in cheltuieli_pe_luni]

    # matplotlib are nevoie de float, nu de Decimal.
    incasari_pe_luni = [float(D(i)) for i in incasari_pe_luni]
    cheltuieli_pe_luni = [float(D(c)) for c in cheltuieli_pe_luni]

    index_col = f"Anul {anul}"

    data = {
        index_col: [
            "Ianuarie",
            "Februarie",
            "Martie",
            "Aprilie",
            "Mai",
            "Iunie",
            "Iulie",
            "August",
            "Septembrie",
            "Octombrie",
            "Noiembrie",
            "Decembrie",
        ],
        "Incasari": incasari_pe_luni,
        "Cheltuieli": cheltuieli_pe_luni,
    }

    # Create DataFrame
    df = pd.DataFrame(data)

    # Set the 'index_col' column as the index
    df.set_index(index_col, inplace=True)

    # Define colors
    dark = "#181c25"
    green = "#33790F"
    amber = "#D8A100"

    # Plot grouped bar chart with custom colors
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(len(df) * 1.5, 6))
    # Set 'Incasari' to green and 'Cheltuieli' to amber
    df.plot(kind="bar", width=0.8, ax=ax, color=[green, amber])

    # Add numbers on the bars, flipped vertically
    for container in ax.containers:
        ax.bar_label(
            container, label_type="edge", rotation=None, color="white", fontsize=10
        )

    # Set labels and title
    ax.set_xlabel(index_col, color="white")
    ax.set_ylabel(f"Suma {currency}", color="white")
    ax.set_title(f"Incasari vs Cheltuieli ({currency})", color="white")

    # Change x-axis label color to white
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    # Change background color to dark
    ax.set_facecolor(dark)
    fig.patch.set_facecolor(dark)

    # Adjust layout to add padding
    plt.tight_layout(pad=3.0)

    # Save the plot as an SVG file
    svgname = f"incasari_vs_cheltuieli_bar_chart_{currency}.svg"
    svgfp = os.path.join(get_media_path(), svgname)
    plt.savefig(svgfp, format="svg")
    plt.close(fig)

    from utils.multiuser import get_user_media_prefix

    return "/media/" + get_user_media_prefix() + svgname
