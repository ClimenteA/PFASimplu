from django.shortcuts import render, HttpResponseRedirect
from django.contrib import messages
from django.views import View
from .forms import SetariForm
from .models import SetariModel
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from documente.models import DocumenteModel
from facturi.models import FacturaModel
from utils.localitati import lista_localitati
from utils.data_import_v1 import DataImportV1


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
        return HttpResponseRedirect("/setari/")


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
            return render(request, "setari.html", {"setari_form": form, "lista_localitati": lista_localitati})

        SetariModel.objects.all().delete()
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return HttpResponseRedirect("/setari/")


class SetariViewDropData(View):

    def post(self, request):

        SetariModel.objects.all().delete()
        CheltuialaModel.objects.all().delete()
        IncasariModel.objects.all().delete()
        DocumenteModel.objects.all().delete()
        FacturaModel.objects.all().delete()

        return HttpResponseRedirect("/setari/")

