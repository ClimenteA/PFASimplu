import logging

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.utils import timezone
from django.views import View

from facturi.models import FacturaModel
from setari.models import SetariModel
from utils.tva import get_luni_cu_facturi_ue
from utils.tva_documente import genereaza_pachet_d390_incasari
from utils.views import (
    download_model_csv_or_xlsx,
    get_cautare,
    get_page_items,
    handle_delete_id_query_param,
)

from .forms import IncasariForm
from .models import IncasariModel

logger = logging.getLogger(__name__)

CAUTARE_COLOANE = {
    "suma": ("Primit", ["suma"]),
    "valuta": ("Valuta", ["valuta"]),
    "data_incasarii": ("Incasare la", ["data_incasarii"]),
    "nume_incasare": ("Nume incasare", ["nume_incasare"]),
    "ue": ("VIES", ["bool:factura__client_ue"]),
    "sursa_venit": ("Venit din", ["sursa_venit"]),
    "actualizat_la": ("Data Modificare", ["actualizat_la"]),
}


def _context_ue(request) -> dict:
    """Contextul filtrului „Incasari din UE (TVA)": incasarile din facturile
    emise catre clienti UE, grupate pe luna de raportare (data emiterii)."""
    ue = request.GET.get("ue") == "1"
    ani_ue = sorted(
        set(
            FacturaModel.objects.filter(client_ue=True).values_list(
                "data_emitere__year", flat=True
            )
        )
        | {timezone.now().year},
        reverse=True,
    )
    anul_ue = int(request.GET.get("anul_ue") or ani_ue[0])
    luni_ue = get_luni_cu_facturi_ue(anul_ue)
    luna_param = request.GET.get("luna_ue")
    luna_ue = int(luna_param) if luna_param else None

    rezultate = IncasariModel.objects.none()
    if ue:
        rezultate = IncasariModel.objects.filter(
            factura__client_ue=True, factura__data_emitere__year=anul_ue
        )
        if luna_ue:
            rezultate = rezultate.filter(factura__data_emitere__month=luna_ue)

    return {
        "ue": ue,
        "ani_ue": ani_ue,
        "anul_ue": anul_ue,
        "luni_ue": luni_ue,
        "luna_ue": luna_ue,
        "ue_results": rezultate,
    }


class IncasariDescarcareView(View):
    def get(self, request):
        return download_model_csv_or_xlsx(request, IncasariModel, "incasari")


class IncasariUEDescarcaView(View):
    """Descarca D390 VIES completat pentru facturile emise catre clienti UE in
    luna selectata, impreuna cu facturile atasate (documente justificative)."""

    def get(self, request):
        anul = int(request.GET.get("anul") or timezone.now().year)
        luna = int(request.GET.get("luna"))

        setari = SetariModel.objects.first()
        if not setari:
            messages.add_message(
                request,
                messages.ERROR,
                "Introdu mai intai datele PFA-ului in Setari!",
                extra_tags="🟥 Date necompletate!",
            )
            return HttpResponseRedirect("/setari/")

        pachet = genereaza_pachet_d390_incasari(anul, luna, setari)
        if not pachet:
            messages.add_message(
                request,
                messages.ERROR,
                "Nu exista facturi cu Client UE VIES pentru luna selectata.",
                extra_tags="🟥 Eroare!",
            )
            return HttpResponseRedirect("/incasari/")

        for observatie in pachet["d390"]["observatii"]:
            messages.add_message(
                request, messages.WARNING, observatie, extra_tags="⚠️ Atentie!"
            )

        with open(pachet["zip_path"], "rb") as f:
            response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = (
            f"attachment; filename=D390_{anul}_{luna:02d}.zip"
        )
        return response


class IncasariView(View):
    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, IncasariModel)
        if redirect_from_delete:
            return redirect_from_delete

        q_cautare, context_cautare = get_cautare(request, CAUTARE_COLOANE)
        form, page_items = get_page_items(
            request, IncasariForm, IncasariModel, cautare=q_cautare
        )

        # Filtrul „Incasari din UE (TVA)" inlocuieste tabelul de mai jos cu
        # incasarile din facturile cu Client UE, la fel ca la Cheltuieli.
        context_ue = _context_ue(request)
        if context_ue["ue"]:
            page_items = Paginator(
                context_ue["ue_results"]
                .filter(q_cautare)
                .order_by("-factura__data_emitere", "-actualizat_la"),
                20,
            ).get_page(request.GET.get("page") or 1)

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
            form = IncasariForm(
                initial={
                    "nume_incasare": factura.nume,
                    "suma": factura.total_de_plata,
                    "valuta": factura.valuta,
                    "tip_tranzactie": factura.tip_tranzactie,
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
                **context_ue,
                **context_cautare,
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
            logger.warning("Formular incasare invalid: %s", form.errors)
            fields_with_errors = [field for field in form.errors]
            if (
                "fisier" in fields_with_errors
                and len(fields_with_errors) == 1
                and (request.GET.get("id") or factura_id)
            ):
                pass
            else:
                q_cautare, context_cautare = get_cautare(request, CAUTARE_COLOANE)
                _, page_items = get_page_items(
                    request, IncasariForm, IncasariModel, cautare=q_cautare
                )
                context_ue = _context_ue(request)
                if context_ue["ue"]:
                    page_items = Paginator(
                        context_ue["ue_results"]
                        .filter(q_cautare)
                        .order_by("-factura__data_emitere", "-actualizat_la"),
                        20,
                    ).get_page(request.GET.get("page") or 1)
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
                        **_context_ue(request),
                        **context_cautare,
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
