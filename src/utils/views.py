import itertools
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode

import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import FileField, Model, Q
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from core.settings import get_extracts_path

from .decimale import format_suma, rotund2
from .pretty_excel import make_excel_pretty


def one_month_from_now():
    return timezone.now() + timedelta(days=30)


def handle_delete_id_query_param(
    request, theModel: Model, redirect_to: str | None = None
):

    redirect_mapper = {
        "DocumenteModel": "/documente/",
        "IncasariModel": "/incasari/",
        "CheltuialaModel": "/cheltuieli/",
        "FacturaModel": "/facturi/",
    }

    if request.GET.get("delete_id"):
        item = get_object_or_404(theModel, id=request.GET.get("delete_id"))
        item.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Intrarea a fost stearsa!",
            extra_tags="✅ Succes!",
        )

        return redirect(
            redirect_to if redirect_to else redirect_mapper[theModel.__qualname__]
        )


PARAMETRI_PASTRATI = (
    "id",
    "factura_id",
    "extern",
    "anul_extern",
    "luna_extern",
    "ue",
    "anul_ue",
    "luna_ue",
)


def get_cautare(request, coloane: dict[str, tuple[str, list[str]]]):
    """Construieste cautarea intr-un tabel, pe coloanele definite de apelant.

    Cheia din `coloane` este valoarea din select, iar valoarea este
    (eticheta afisata, campuri ORM in care se cauta). Cand selectul nu are
    nicio valoare, cautarea se face in toate campurile tuturor coloanelor.
    Intoarce (query-ul de aplicat pe queryset, contextul pentru template).
    """
    cauta = (request.GET.get("cauta") or "").strip()
    coloana = request.GET.get("coloana") or ""
    if coloana not in coloane:
        coloana = ""

    campuri = (
        coloane[coloana][1]
        if coloana
        else [
            camp for _, campuri_coloana in coloane.values() for camp in campuri_coloana
        ]
    )

    query = Q()
    if cauta:
        for camp in campuri:
            if camp.startswith("bool:"):
                # Coloanele boolean (ex. „UE") se cauta cu da/nu, nu cu text.
                nume = camp.removeprefix("bool:")
                valoare = cauta.lower()
                if valoare in ("ue", "da", "1", "true", "yes"):
                    query |= Q(**{nume: True})
                elif valoare in ("non-ue", "non ue", "nu", "0", "false", "no"):
                    query |= Q(**{nume: False}) | Q(**{f"{nume}__isnull": True})
            else:
                query |= Q(**{f"{camp}__icontains": cauta})

    # Pastram filtrele deja active (editare, precompletare, filtrul TVA) la
    # submiterea cautarii si la schimbarea paginii. `delete_id` nu e in lista
    # ca sa nu se sterga inregistrari din greseala la paginare.
    pastrati = {
        cheie: request.GET[cheie]
        for cheie in PARAMETRI_PASTRATI
        if request.GET.get(cheie)
    }
    parametrii_url = dict(pastrati)
    if cauta:
        parametrii_url["cauta"] = cauta
    if coloana:
        parametrii_url["coloana"] = coloana

    context = {
        "cauta": cauta,
        "coloana": coloana,
        "coloane_cautare": [(cheie, date[0]) for cheie, date in coloane.items()],
        "parametri_pastrati": list(pastrati.items()),
        "query_cautare": urlencode(parametrii_url),
    }
    return query, context


def get_page_items(
    request,
    theForm: ModelForm,
    theModel: Model,
    order_by: str = "-data_inserarii",
    cautare: Q | None = None,
):

    item_id = request.GET.get("id")
    page_number = request.GET.get("page")

    if not page_number:
        page_number = 1

    if item_id:
        item = get_object_or_404(theModel, id=item_id)
        form = theForm(instance=item)
    else:
        if theForm.__qualname__ == "CheltuieliForm":
            form = theForm(initial={"data_inserarii": timezone.now().date()})
        elif theForm.__qualname__ == "FacturaForm":
            serie = "INV"
            numar = 1
            latest_invoice = theModel.objects.order_by("-numar").first()
            if latest_invoice:
                serie = latest_invoice.serie
                numar = latest_invoice.numar + 1

            form = theForm(
                initial={
                    "serie": serie,
                    "numar": numar,
                    "data_emitere": timezone.now().date(),
                    "data_scadenta": one_month_from_now().date(),
                }
            )
        else:
            form = theForm()

    if theModel.__qualname__ == "IncasariModel":
        neincasate = theModel.objects.filter(data_incasarii__isnull=True).order_by(
            "-actualizat_la"
        )
        incasate = theModel.objects.filter(data_incasarii__isnull=False).order_by(
            order_by
        )
        if cautare is not None:
            neincasate = neincasate.filter(cautare)
            incasate = incasate.filter(cautare)
        results = list(itertools.chain(neincasate, incasate))
    else:
        results = theModel.objects.all().order_by(order_by)
        if cautare is not None:
            results = results.filter(cautare)

    paginator = Paginator(results, 20)
    page_items = paginator.get_page(page_number)

    return form, page_items


def pregateste_df_export(df: pd.DataFrame, pentru_csv: bool = False) -> pd.DataFrame:
    """Rotunjeste la 2 zecimale toate celulele ``Decimal`` dintr-un DataFrame.

    Pentru CSV scriem textul fara zerouri inutile (``12.35``, ``100``), iar
    pentru XLSX lasam numere reale, ca sa poata fi folosite in formule.
    """
    df = df.copy()
    for coloana in df.columns:
        df[coloana] = df[coloana].map(
            lambda v: (
                (format_suma(v) if pentru_csv else float(rotund2(v)))
                if isinstance(v, Decimal)
                else v
            )
        )
    return df


def download_dataframe(request, df: pd.DataFrame, filename: str):
    """Scrie DataFrame-ul intr-un singur CSV sau XLSX (dupa ?filetype=) si il
    trimite direct ca fisier, fara arhiva zip."""
    filetype = (request.GET.get("filetype") or "").lower()

    if filetype not in ["csv", "xlsx"]:
        return redirect("/registre/")

    extracts_folder = get_extracts_path()
    filepath = os.path.join(extracts_folder, f"{filename}.{filetype}")

    if filetype == "csv":
        content_type = "text/csv"
        pregateste_df_export(df, pentru_csv=True).to_csv(filepath, index=False)
    else:
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        pregateste_df_export(df).to_excel(filepath, index=False)
        make_excel_pretty(filepath, number_format="General")

    response = HttpResponse(open(filepath, "rb"), content_type=content_type)
    response["Content-Disposition"] = (
        f"attachment; filename={os.path.basename(filepath)}"
    )
    return response


def download_csv_or_xlsx(request, df: pd.DataFrame, filename: str):
    anul = request.GET.get("anul")
    anul = int(anul) if anul else timezone.now().year

    if filename != "registru_inventar":
        filename = f"{anul}_{filename}"

    return download_dataframe(request, df, filename)


def model_dataframe(theModel: Model, order_by: str = "-data_inserarii") -> pd.DataFrame:
    """Construieste DataFrame-ul cu toate inregistrarile modelului, curatand
    campurile care nu pot fi scrise direct in CSV/XLSX."""
    data = list(theModel.objects.all().order_by(order_by).values())

    campuri_fisier = {
        field.attname for field in theModel._meta.fields if isinstance(field, FileField)
    }

    # openpyxl nu accepta datetime cu timezone sau liste/dict-uri direct in
    # celule; le convertim la valori care pot fi scrise in Excel/CSV.
    for item in data:
        for key, value in item.items():
            if key in campuri_fisier and value:
                item[key] = os.path.basename(value)
            elif isinstance(value, datetime) and value.tzinfo is not None:
                item[key] = value.replace(tzinfo=None)
            elif isinstance(value, (list, dict)):
                item[key] = json.dumps(value, ensure_ascii=False)

    return pd.DataFrame(data)


def download_model_csv_or_xlsx(
    request, theModel: Model, filename: str, order_by: str = "-data_inserarii"
):
    """Exporta toate inregistrarile modelului intr-un singur CSV/XLSX,
    fara paginare si fara zip."""
    filetype = (request.GET.get("filetype") or "").lower()

    if filetype not in ["csv", "xlsx"]:
        return redirect("/registre/")

    df = model_dataframe(theModel, order_by)
    return download_dataframe(request, df, filename)
