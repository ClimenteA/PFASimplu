from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from utils.views import get_page_items, download_zip, handle_delete_id_query_param
from .forms import CheltuieliForm
from .models import CheltuialaModel, TipAchizitie


class CheltuieliDescarcareView(View):

    def get(self, request):
        return download_zip(request, CheltuialaModel)


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
        return render(
            request,
            template_name="cheltuieli.html",
            context={
                "cheltuieli_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
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
