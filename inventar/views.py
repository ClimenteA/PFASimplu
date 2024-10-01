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
from core.settings import MEDIA_ROOT
from zipfile import ZipFile
from fpdf_table import PDFTable, Align



class InventarDescarcaFisierView(View):

    def get(self, request):
        nr_inventar = request.GET.get("nr_inventar")
        db_id = request.GET.get("db_id")

        inv = CheltuialaModel.objects.filter(id=db_id).first()

        fel_document = f"{inv.nume_cheltuiala} {inv.data_inserarii.isoformat()}"

        pdf = PDFTable()

        pdf.add_fonts_custom(
            font_name="arial", 
            font_extension="ttf", 
            font_dir=os.path.join("static", "arial-font"), 
            set_default=True
        )

        # Date identificare factura
        pdf.table_header(["FIŞA MIJLOCULUI FIX"], align=Align.L)
        pdf.table_row([''])
        pdf.table_row(['Nr. Inventar: ', str(nr_inventar)])
        pdf.table_row(['Fel, serie, nr. data document provenienţă: ', fel_document])
        pdf.table_row(['Valoare de inventar: ', str(inv.suma_in_ron)])
        pdf.table_row(['Amortizare lunară: ', str(inv.amortizare_lunara)])
        pdf.table_row(['Denumirea mijlocului fix şi caracteristici tehnice: ', "Detaliate in factura/bon."])
        pdf.table_row(['Accesorii: ', "Detaliate in factura/bon."])
        pdf.table_row(['Grupa: ', inv.grupa], option='responsive')
        pdf.table_row(['Codul de clasificare: ', inv.cod_de_clasificare])
        pdf.table_row(['Anul dării în folosinţă: ', str(inv.anul_darii_in_folosinta)])
        pdf.table_row(['Luna dării în folosinţă: ', str(inv.luna_darii_in_folosinta)])
        pdf.table_row(['Anul amortizării complete: ', str(inv.anul_amortizarii_complete)])
        pdf.table_row(['Luna amortizării complete: ', str(inv.luna_amortizarii_complete)])
        pdf.table_row(['Durata normală de funcţionare: ', inv.durata_normala_de_functionare])
        pdf.table_row(['Cota de amortizare: ', str(inv.cota_de_amortizare)])

        pdf.table_row([''])
        
        width_cols = pdf.table_cols(1, 3, 3.5, 0.5, 1, 1, 1, 1)
        pdf.set_font(pdf.font, "B", pdf.text_normal_size)

        mutari_header = [
            "Nr.inventar (de la număr la număr)",
            "Documentul (data, felul, numărul)",
            "Operaţiunile care privesc mişcarea, creşterea sau diminuarea valorii mijlocului fix",
            "Buc.",
            "Debit",
            "Credit",
            "Sold",
            'Soldul contului 105 "Rezerve din reevaluare"'
        ]

        pdf.table_row(mutari_header, width_cols, option='responsive')
        pdf.set_font(pdf.font, "", pdf.text_normal_size)
        
        empty_rows = [""]*len(mutari_header)
        for _ in range(20): 
            pdf.table_row(empty_rows, width_cols)

        save_pdf_path = os.path.join(MEDIA_ROOT, "fisa_mijloc_fix.pdf")
        pdf.output(save_pdf_path)

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
        ).order_by("-data_inserarii")

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
