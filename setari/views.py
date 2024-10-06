import os
import shutil
import zipfile
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.views import View
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from documente.models import DocumenteModel
from facturi.models import FacturaModel
from utils.localitati import lista_localitati
from utils.data_import_v1 import DataImportV1
from utils.data_import_v2 import DataImportV2
from .forms import SetariForm
from .models import SetariModel
from core.settings import MEDIA_ROOT, make_media_dir, get_extracts_path
import pandas as pd


class ImportV1View(View):

    def post(self, request):
        dim1 = DataImportV1()

        dim1.insert_date_pfa()
        dim1.insert_incasari()
        dim1.insert_cheltuieli()
        dim1.insert_documente()

        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele din folderul stocare au fost adaugate!",
            extra_tags="✅ Succes!",
        )
        return redirect("/setari/")


class ImportV2View(View):

    def post(self, request):
        dim2 = DataImportV2()

        dim2.insert_date_pfa()
        dim2.insert_incasari()
        dim2.insert_cheltuieli()
        dim2.insert_documente()

        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele din folderul stocare au fost adaugate!",
            extra_tags="✅ Succes!",
        )
        return redirect("/setari/")



class SetariView(View):

    def get(self, request):
        result = SetariModel.objects.first()
        form = SetariForm(instance=result)
        return render(
            request,
            template_name="setari.html",
            context={"setari_form": form, "lista_localitati": lista_localitati},
        )

    def post(self, request, *args, **kwargs):
        form = SetariForm(request.POST)

        if not form.is_valid():
            print("------", form.errors)
            return render(
                request,
                "setari.html",
                {"setari_form": form, "lista_localitati": lista_localitati},
            )

        SetariModel.objects.all().delete()

        form.save()
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

        def save_model_to_csv(model, filename):
            data = model.objects.all()
            for item in data:
                shutil.copy2(item.fisier.path, os.path.join(storage_path, os.path.basename(item.fisier.path))) 
                
            df = pd.DataFrame(data.values())
            df.to_csv(os.path.join(storage_path, filename), index=False)

        save_model_to_csv(CheltuialaModel, "Cheltuiala.csv")
        save_model_to_csv(IncasariModel, "Incasari.csv")
        save_model_to_csv(DocumenteModel, "Documente.csv")

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
