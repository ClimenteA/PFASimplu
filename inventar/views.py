import os
from django.shortcuts import render
from cheltuieli.models import CheltuialaModel
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from .forms import InventarForm
from django.utils import timezone
from utils.views import handle_delete_id_query_param
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from utils.pdf_from_html import create_pdf_from_html
from core.settings import MEDIA_ROOT
from zipfile import ZipFile



class InventarDescarcaFisierView(View):

    def get(self, request):
        nr_inventar = request.GET.get("nr_inventar")
        db_id = request.GET.get("db_id")

        inv = CheltuialaModel.objects.filter(id=db_id).first()

        fel_document = f"{inv.nume_cheltuiala} {inv.data_inserarii.isoformat()}"

        context = {
            "numar_inventar": nr_inventar,
            "fel_document": fel_document,
            "valoare_inventar": inv.suma_in_ron,
            "amortizare_lunara": inv.amortizare_lunara,
            "denumire_si_caracteristici_tehnice": "Detaliate in factura/bon.",
            "accesorii": "Detaliate in factura/bon.",
            "grupa": inv.grupa,
            "cod_de_clasificare": inv.cod_de_clasificare,
            "anul_darii_in_folosinta": inv.anul_darii_in_folosinta,
            "luna_darii_in_folosinta": inv.luna_darii_in_folosinta,
            "anul_amortizarii_complete": inv.anul_amortizarii_complete,
            "luna_amortizarii_complete": inv.luna_amortizarii_complete,
            "durata_normala_de_functionare": inv.durata_normala_de_functionare,
            "cota_de_amortizare": inv.cota_de_amortizare,
            "blank_rows": list(range(30))
        }

        factura_content = render_to_string("fisa_mijloc_fix_pdf.html", context)
        save_pdf_path = os.path.join(MEDIA_ROOT, "fisa_mijloc_fix.pdf")
        save_pdf_path = create_pdf_from_html(factura_content, save_pdf_path)

        extracts_folder = os.path.join(MEDIA_ROOT, "extracts")
        os.makedirs(extracts_folder, exist_ok=True)

        files = [save_pdf_path, inv.fisier.path]
        zip_filepath = os.path.join(extracts_folder, f"{fel_document}.zip")
        with ZipFile(zip_filepath, "w") as zipf:
            for file in files:
                zipf.write(file, os.path.basename(file))

        response = HttpResponse(
            open(zip_filepath, "rb"), content_type="application/zip"
        )
        response["Content-Disposition"] = (
            f"attachment; filename={os.path.basename(zip_filepath)}"
        )
        return response


class InventarView(View):

    def get(self, request):

        redirect_from_delete = handle_delete_id_query_param(request, CheltuialaModel, redirect_to="/inventar/")
        if redirect_from_delete:
            return redirect_from_delete
        
        page_number = request.GET.get("page")
        item_id = request.GET.get("id")

        if item_id:
            item = get_object_or_404(CheltuialaModel, id=item_id)
            form = InventarForm(instance=item)
        else:
            form = InventarForm(initial={"data_iesirii_din_uz": timezone.now().date()})

        if not page_number:
            page_number = 1

        results = CheltuialaModel.objects.filter(
            Q(obiect_de_inventar=True) | Q(mijloc_fix=True)
        ).order_by("-actualizat_la")

        paginator = Paginator(results, 100)
        page_items = paginator.get_page(page_number)

        return render(
            request,
            template_name="inventar.html",
            context={
                "inventar_form": form,
                "page_items": page_items,
                "item_id": item_id,
            },
        )

    def post(self, request):

        # Update
        item_id = request.GET.get("id")
        item = get_object_or_404(CheltuialaModel, id=item_id)
        form = InventarForm(request.POST, request.FILES, instance=item)

        # Invalid
        if not form.is_valid():
            fields_with_errors = [field for field in form.errors]
            if (
                "nume_cheltuiala" in fields_with_errors
                and len(fields_with_errors) == 1
                and item_id
            ):
                pass
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Nu am putut scoate din inventar..",
                    extra_tags="🟥 Eroare!",
                )
                return HttpResponseRedirect("/inventar/")

        # Save
        form.instance.nume_cheltuiala = item.nume_cheltuiala
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return HttpResponseRedirect("/inventar/")
