from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.utils import timezone
from django.views import View

from facturi.models import FacturaModel, ModalitatePlata
from utils.valuta import TipTranzactie
from utils.views import (
    download_model_csv_or_xlsx,
    get_page_items,
    handle_delete_id_query_param,
)

from .forms import IncasariForm
from .models import IncasariModel


class IncasariDescarcareView(View):
    def get(self, request):
        return download_model_csv_or_xlsx(request, IncasariModel, "incasari")


class IncasariView(View):
    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, IncasariModel)
        if redirect_from_delete:
            return redirect_from_delete

        form, page_items = get_page_items(request, IncasariForm, IncasariModel)

        # Precompletare din factura (butonul "Incasata" din pagina Facturi)
        factura_id = request.GET.get("factura_id")
        fisier_factura = None
        nume_fisier_factura = None
        if factura_id:
            factura = get_object_or_404(FacturaModel, id=factura_id)
            if IncasariModel.objects.filter(factura=factura).exists():
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Aceasta factura are deja o incasare inregistrata! "
                    "Sterge incasarea existenta daca vrei sa o adaugi din nou.",
                    extra_tags="⚠️ Atentie!",
                )
                return HttpResponseRedirect("/incasari/")
            tip_tranzactie = (
                TipTranzactie.BANCAR.value
                if factura.tip_tranzactie == ModalitatePlata.BANCAR.value
                else TipTranzactie.NUMERAR.value
            )
            form = IncasariForm(
                initial={
                    "suma": factura.total_de_plata,
                    "valuta": factura.valuta,
                    "tip_tranzactie": tip_tranzactie,
                    "data_inserarii": timezone.now().date(),
                }
            )
            if factura.fisier_factura_pdf:
                fisier_factura = factura.fisier_factura_pdf
                nume_fisier_factura = f"factura_{factura.serie}-{factura.numar}.pdf"

        return render(
            request,
            template_name="incasari.html",
            context={
                "incasari_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
                "factura_id": factura_id,
                "fisier_factura": fisier_factura,
                "nume_fisier_factura": nume_fisier_factura,
            },
        )

    def post(self, request):

        if request.GET.get("id"):
            # Update
            item = get_object_or_404(IncasariModel, id=request.GET.get("id"))
            form = IncasariForm(request.POST, request.FILES, instance=item)
        else:
            # Insert
            form = IncasariForm(request.POST, request.FILES)

        # Atasam PDF-ul facturii daca incasarea vine din pagina Facturi.
        # Folosim o copie (ContentFile) ca incasarea sa aiba propriul fisier,
        # nu o referinta la fisierul facturii (care ar fi sters odata cu factura).
        factura_id = request.GET.get("factura_id")
        factura = None
        if factura_id and not request.GET.get("id"):
            factura = get_object_or_404(FacturaModel, id=factura_id)
            if IncasariModel.objects.filter(factura=factura).exists():
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Aceasta factura are deja o incasare inregistrata! "
                    "Sterge incasarea existenta daca vrei sa o adaugi din nou.",
                    extra_tags="⚠️ Atentie!",
                )
                return HttpResponseRedirect("/incasari/")
            if not request.FILES.get("fisier") and factura.fisier_factura_pdf:
                with factura.fisier_factura_pdf.open("rb") as pdf:
                    form.files["fisier"] = ContentFile(
                        pdf.read(), name=f"factura_{factura.serie}-{factura.numar}.pdf"
                    )

        # Invalid
        if not form.is_valid():
            print(form)
            fields_with_errors = [field for field in form.errors]
            if (
                "fisier" in fields_with_errors
                and len(fields_with_errors) == 1
                and (request.GET.get("id") or factura_id)
            ):
                pass
            else:
                _, page_items = get_page_items(request, IncasariForm, IncasariModel)
                return render(
                    request,
                    "incasari.html",
                    {
                        "incasari_form": form,
                        "page_items": page_items,
                        "item_id": request.GET.get("id"),
                        "factura_id": factura_id,
                        "fisier_factura": factura.fisier_factura_pdf
                        if factura
                        else None,
                        "nume_fisier_factura": (
                            f"factura_{factura.serie}-{factura.numar}.pdf"
                            if factura and factura.fisier_factura_pdf
                            else None
                        ),
                    },
                )

        # Save
        incasare = form.save(commit=False)
        if factura:
            incasare.factura = factura
        incasare.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return HttpResponseRedirect("/incasari/")
