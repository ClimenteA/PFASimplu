import os
import shutil
import zipfile
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.views import View
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from documente.models import DocumenteModel
from facturi.models import FacturaModel
from utils.localitati import lista_localitati
from utils.valuta import Valuta
from utils.trezorerie import (
    get_link_iban_trezorerie,
    get_iban_trezorerie_pentru_localitate,
    asigura_date_iban_trezorerie,
    COD_BUGETAR_TVA,
    ANAF_CODURI_IBAN,
)
from .forms import SetariForm
from .models import SetariModel
from core.settings import MEDIA_ROOT, make_media_dir, get_extracts_path
import pandas as pd


lista_valute = [choice.value for choice in Valuta]


def get_setari_context(form):
    result = SetariModel.objects.first()
    localitate = form.initial.get("localitate") or (result.localitate if result else "")
    return {
        "setari_form": form,
        "lista_localitati": lista_localitati,
        "lista_valute": lista_valute,
        "link_iban_trezorerie": get_link_iban_trezorerie(localitate),
        "cod_bugetar_tva": COD_BUGETAR_TVA,
    }


class SetariIbanTrezorerieView(View):
    """Cand utilizatorul selecteaza localitatea, intoarce IBAN-ul trezoreriei
    pentru plata TVA (extras din sursele oficiale ANAF) + linkul de verificare."""

    def get(self, request):
        localitate = request.GET.get("localitate", "")
        potrivire = get_iban_trezorerie_pentru_localitate(localitate)
        return JsonResponse({
            "iban": potrivire["iban"] if potrivire else None,
            "nume_trezorerie": potrivire["nume_trezorerie"] if potrivire else None,
            "sursa": potrivire["sursa"] if potrivire else get_link_iban_trezorerie(localitate),
            "pagina_anaf": ANAF_CODURI_IBAN,
            "cod_bugetar": COD_BUGETAR_TVA,
        })


class SetariView(View):

    def get(self, request):
        result = SetariModel.objects.first()
        form = SetariForm(instance=result)
        return render(
            request,
            template_name="setari.html",
            context=get_setari_context(form),
        )

    def post(self, request, *args, **kwargs):
        form = SetariForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                "setari.html",
                context=get_setari_context(form),
            )

        setari = form.save(commit=False)

        # Daca IBAN-ul trezoreriei nu a fost completat (utilizatorul a salvat
        # fara sa selecteze din nou localitatea), il deducem automat din
        # localitate, din tabelul extras din sursele oficiale ANAF.
        if not setari.cont_iban_trezoreria:
            # Daca tabelul iban_trezorerie.json lipseste, il descarcam acum
            # de pe ANAF (o singura data; apoi ramane salvat local).
            if not asigura_date_iban_trezorerie():
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Nu am putut descarca lista IBAN-urilor trezoreriilor de pe ANAF "
                    "(lipsa conexiune?). Completeaza IBAN-ul trezoreriei manual din "
                    "lista ANAF, sau salveaza din nou cand ai conexiune la internet.",
                    extra_tags="⚠️ Atentie!",
                )
            potrivire = get_iban_trezorerie_pentru_localitate(setari.localitate)
            if potrivire:
                setari.cont_iban_trezoreria = potrivire["iban"]

        SetariModel.objects.all().delete()

        setari.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return redirect("/setari/")



class SetariViewDownloadData(View):

    def post(self, request):

        extracts_path = get_extracts_path()
        storage_path = os.path.join(extracts_path, "stocare")
        os.makedirs(storage_path, exist_ok=True)

        copyfile = lambda fp: shutil.copy2(fp, os.path.join(storage_path, os.path.basename(fp))) 

        def save_model_to_csv(model, filename: str):
            data = model.objects.all()

            if len(data) == 0:
                return
            
            for item in data:
                if hasattr(item, "fisier"):
                    if item.fisier:
                        copyfile(item.fisier.path)
                if hasattr(item, "fisier_efactura_xml"):
                    if item.fisier_efactura_xml:
                        copyfile(item.fisier_efactura_xml.path)
                if hasattr(item, "fisier_factura_pdf"):
                    if item.fisier_factura_pdf:
                        copyfile(item.fisier_factura_pdf.path)
                    
            df = pd.DataFrame(data.values())
            df.to_csv(os.path.join(storage_path, filename), index=False)

        save_model_to_csv(CheltuialaModel, "Cheltuiala.csv")
        save_model_to_csv(IncasariModel, "Incasari.csv")
        save_model_to_csv(DocumenteModel, "Documente.csv")
        save_model_to_csv(FacturaModel, "Factura.csv")

        df = pd.DataFrame(SetariModel.objects.all().values())
        df.to_csv(os.path.join(storage_path, "Setari.csv"), index=False)

        zip_filename = os.path.join(extracts_path, "stocare.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, dirs, files in os.walk(storage_path):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), storage_path))

        with open(zip_filename, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_filename)}'
            return response


class SetariViewDropData(View):

    def post(self, request):

        SetariModel.objects.all().delete()
        CheltuialaModel.objects.all().delete()
        IncasariModel.objects.all().delete()
        DocumenteModel.objects.all().delete()
        FacturaModel.objects.all().delete()

        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        make_media_dir()

        return redirect("/setari/")
