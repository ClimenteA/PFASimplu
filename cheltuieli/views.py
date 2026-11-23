import json

from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.utils import timezone
from setari.models import SetariModel
from utils.tari import TARI_UE_CHOICES, TARI_NON_UE_CHOICES
from utils.tva import (
    get_cheltuieli_taxare_inversa,
    get_luni_cu_taxare_inversa,
    get_observatii_declaratie,
)
from utils.tva_documente import genereaza_pachet_tva
from utils.views import get_page_items, download_zip, handle_delete_id_query_param
from .forms import CheltuieliForm
from .models import CheltuialaModel, TipAchizitie


class CheltuieliDescarcareView(View):

    def get(self, request):
        return download_zip(request, CheltuialaModel)


class CheltuieliTVADescarcaView(View):
    """Descarca declaratiile TVA pentru luna selectata in filtrul din Cheltuieli
    (facturile cu Origine furnizor UE/non-UE): zip cu D301 + D390 (doar UE)
    + jurnal de cumparari + instructiuni de plata.
    - UE: D301 + D390, pe codul special de TVA intracomunitar (art. 317) din Setari;
    - non-UE: doar D301, pe CIF-ul normal din Setari."""

    def get(self, request):
        anul = int(request.GET.get("anul") or timezone.now().year)
        luna = int(request.GET.get("luna"))

        setari = SetariModel.objects.first()
        if not setari:
            messages.add_message(
                request, messages.ERROR,
                "Introdu mai intai datele PFA-ului in Setari!",
                extra_tags="🟥 Date necompletate!",
            )
            return HttpResponseRedirect("/setari/")

        pachet = genereaza_pachet_tva(anul, luna, setari)
        if not pachet:
            messages.add_message(
                request, messages.ERROR,
                "Nu exista cheltuieli cu taxare inversa (UE/non-UE) pentru luna selectata.",
                extra_tags="🟥 Eroare!",
            )
            return HttpResponseRedirect("/cheltuieli/")

        for observatie in get_observatii_declaratie(anul, luna, setari):
            messages.add_message(
                request, messages.WARNING, observatie, extra_tags="⚠️ Atentie!"
            )

        with open(pachet["zip_path"], "rb") as f:
            response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename=D301-D390_{anul}_{luna:02d}.zip'
        )
        return response


class CheltuieliSearchFurnizor(View):
    """Typeahead pentru furnizorii externi: la a doua factura de la acelasi
    furnizor, codul fiscal si tara se precompleteaza din inregistrarile anterioare."""

    def get(self, request, nume_furnizor: str):
        results = (
            CheltuialaModel.objects.filter(
                furnizor_denumire__icontains=nume_furnizor,
                tip_achizitie__in=[TipAchizitie.SERVICII_UE, TipAchizitie.SERVICII_NON_UE],
            )
            .order_by("-data_inserarii")
            .values("furnizor_denumire", "furnizor_cod_fiscal", "furnizor_tara")
        )

        vazute = set()
        unici = []
        for r in results:
            cheie = (r["furnizor_denumire"] or "").strip().upper()
            if cheie and cheie not in vazute:
                vazute.add(cheie)
                unici.append(r)
            if len(unici) >= 10:
                break

        return JsonResponse(unici, safe=False)


class CheltuieliView(View):

    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, CheltuialaModel)
        if redirect_from_delete:
            return redirect_from_delete

        form, page_items = get_page_items(request, CheltuieliForm, CheltuialaModel)

        # Filtrul "Cheltuieli externe (TVA)": pe luni, facturile cu Origine
        # furnizor diferita de Romania, pentru care se depun D301/D390.
        extern = request.GET.get("extern") == "1"
        ani_externi = sorted(
            {
                (c.data_facturii or c.data_inserarii).year
                for c in CheltuialaModel.objects.filter(
                    tip_achizitie__in=[TipAchizitie.SERVICII_UE, TipAchizitie.SERVICII_NON_UE],
                )
                if (c.data_facturii or c.data_inserarii)
            } | {timezone.now().year},
            reverse=True,
        )
        anul_extern = int(request.GET.get("anul_extern") or ani_externi[0])
        luni_extern = get_luni_cu_taxare_inversa(anul_extern)
        luna_param = request.GET.get("luna_extern")
        luna_extern = int(luna_param) if luna_param else None

        if extern:
            results = get_cheltuieli_taxare_inversa(anul_extern, luna_extern)
            page_items = Paginator(results, 100).get_page(request.GET.get("page") or 1)

        return render(
            request,
            template_name="cheltuieli.html",
            context={
                "cheltuieli_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
                "tari_ue_json": json.dumps(TARI_UE_CHOICES),
                "tari_non_ue_json": json.dumps(TARI_NON_UE_CHOICES),
                "extern": extern,
                "ani_externi": ani_externi,
                "anul_extern": anul_extern,
                "luni_extern": luni_extern,
                "luna_extern": luna_extern,
            },
        )

    def post(self, request):

        if request.GET.get("id"):
            # Update
            item = get_object_or_404(CheltuialaModel, id=request.GET.get("id"))
            form = CheltuieliForm(request.POST, request.FILES, instance=item)
        else:
            # Insert
            form = CheltuieliForm(request.POST, request.FILES)

        # Invalid
        if not form.is_valid():
            fields_with_errors = [field for field in form.errors]
            if (
                "fisier" in fields_with_errors
                and len(fields_with_errors) == 1
                and request.GET.get("id")
            ):
                pass
            else:
                _, page_items = get_page_items(request, CheltuieliForm, CheltuialaModel)
                return render(
                    request,
                    "cheltuieli.html",
                    {
                        "cheltuieli_form": form,
                        "page_items": page_items,
                        "item_id": request.GET.get("id"),
                        "tari_ue_json": json.dumps(TARI_UE_CHOICES),
                        "tari_non_ue_json": json.dumps(TARI_NON_UE_CHOICES),
                    },
                )

        # Save
        try:
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Datele au fost salvate!",
                extra_tags="✅ Succes!",
            )
        except Exception as err:
            messages.add_message(
                request,
                messages.ERROR,
                " ".join(err) if hasattr(err, "__iter__") else str(err),
                extra_tags="🟥 Eroare!",
            )

        return HttpResponseRedirect("/cheltuieli/")
