import os
import itertools
import pandas as pd
from datetime import datetime, timedelta
from zipfile import ZipFile
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


def download_csv_or_xlsx(request, df: pd.DataFrame, filename: str):
    anul = request.GET.get("anul")
    anul = int(anul) if anul else timezone.now().year
    filetype = request.GET.get("filetype").lower()

    if filetype not in ["csv", "xlsx"]:
        return redirect("/registre/")

    extracts_folder = get_extracts_path()

    if filename == "registru_inventar":
        filename = f"{filename}.{filetype}"
    else:
        filename = f"{anul}_{filename}.{filetype}"

    filepath = os.path.join(extracts_folder, filename)

    content_type = "application/octet-stream"

    if filetype == "csv":
        content_type = "text/csv"
        df.to_csv(filepath, index=False)
    if filetype == "xlsx":
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




def download_zip(request, theModel: Model, order_by: str = "-data_inserarii"):
    results = theModel.objects.all().order_by(order_by)
    paginator = Paginator(results, 500_000)
    filetype = request.GET.get("filetype").lower()

    if filetype not in ["csv", "xlsx"]:        
        return redirect("/registre/")

    page_number = 1
    extracts_folder = get_extracts_path()

    files = []

    while True:
        page_items = paginator.get_page(page_number)
        if not page_items:
            break

        # Convert datetime fields to be timezone-unaware
        data = list(page_items.object_list.values())
        for item in data:
            for key, value in item.items():
                if isinstance(value, datetime) and value.tzinfo is not None:
                    item[key] = value.replace(tzinfo=None)

        df = pd.DataFrame(data)
        filename = os.path.join(extracts_folder, f"page_{page_number}.{filetype}")
        
        if filetype == "csv":
            df.to_csv(filename, index=False)
        if filetype == "xlsx":
            df.to_excel(filename, index=False)
            make_excel_pretty(filename)

        files.append(filename)

        if not page_items.has_next():
            break

        page_number += 1

    zip_filename = os.path.join(extracts_folder, f"{theModel.__qualname__.replace('Model', '')}.zip")
    with ZipFile(zip_filename, "w") as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))

    response = HttpResponse(
        open(zip_filename, "rb"), content_type="application/zip"
    )
    response["Content-Disposition"] = (
        f"attachment; filename={os.path.basename(zip_filename)}"
    )
    return response
