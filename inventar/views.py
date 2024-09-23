from django.shortcuts import render
from cheltuieli.models import CheltuialaModel
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from .forms import InventarForm
from django.utils import timezone
from utils.views import handle_delete_id_query_param

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
