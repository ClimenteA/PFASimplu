from django.views import View
from django.contrib import messages
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from utils.views import get_page_items, download_zip, handle_delete_id_query_param
from .forms import IncasariForm
from .models import IncasariModel


class IncasariDescarcareView(View):

    def get(self, request):
        return download_zip(request, IncasariModel)


class IncasariView(View):

    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, IncasariModel)
        if redirect_from_delete:
            return redirect_from_delete
        
        form, page_items = get_page_items(request, IncasariForm, IncasariModel)
        return render(
            request,
            template_name="incasari.html",
            context={
                "incasari_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
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

        # Invalid
        if not form.is_valid():
            print(form)
            fields_with_errors = [field for field in form.errors]
            if (
                "fisier" in fields_with_errors
                and len(fields_with_errors) == 1
                and request.GET.get("id")
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
                    },
                )

        # Save
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return HttpResponseRedirect("/incasari/")
