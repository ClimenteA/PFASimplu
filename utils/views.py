import json
import os
import itertools
import pandas as pd
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.forms import ModelForm
from django.db.models import Model
from django.contrib import messages
from core.settings import get_extracts_path
from .pretty_excel import make_excel_pretty


def one_month_from_now():
    return timezone.now() + timedelta(days=30)


def handle_delete_id_query_param(request, theModel: Model, redirect_to: str = None):

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

        return redirect(redirect_to if redirect_to else redirect_mapper[theModel.__qualname__])



def get_page_items(request, theForm: ModelForm, theModel: Model, order_by: str = "-data_inserarii"):

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
            latest_invoice = theModel.objects.order_by('-numar').first()
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
        neincasate = theModel.objects.filter(data_inserarii__isnull=True).order_by("-actualizat_la")
        incasate = theModel.objects.filter(data_inserarii__isnull=False).order_by(order_by)
        results = list(itertools.chain(neincasate, incasate))
    else:
        results = theModel.objects.all().order_by(order_by)

    paginator = Paginator(results, 100)
    page_items = paginator.get_page(page_number)

    return form, page_items


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
        df.to_csv(filepath, index=False)
    else:
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        df.to_excel(filepath, index=False)
        make_excel_pretty(filepath)

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


def download_model_csv_or_xlsx(
    request, theModel: Model, filename: str, order_by: str = "-data_inserarii"
):
    """Exporta toate inregistrarile modelului intr-un singur CSV/XLSX,
    fara paginare si fara zip."""
    filetype = (request.GET.get("filetype") or "").lower()

    if filetype not in ["csv", "xlsx"]:
        return redirect("/registre/")

    data = list(theModel.objects.all().order_by(order_by).values())

    # openpyxl nu accepta datetime cu timezone sau liste/dict-uri direct in
    # celule; le convertim la valori care pot fi scrise in Excel/CSV.
    for item in data:
        for key, value in item.items():
            if isinstance(value, datetime) and value.tzinfo is not None:
                item[key] = value.replace(tzinfo=None)
            elif isinstance(value, (list, dict)):
                item[key] = json.dumps(value, ensure_ascii=False)

    df = pd.DataFrame(data)
    return download_dataframe(request, df, filename)
