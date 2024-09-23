from django.views import View
from django.contrib import messages
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from utils.views import get_page_items, handle_delete_id_query_param
from .forms import DocumenteForm
from .models import DocumenteModel


class DocumenteView(View):

    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, DocumenteModel)
        if redirect_from_delete:
            return redirect_from_delete
        
        form, page_items = get_page_items(
            request, DocumenteForm, DocumenteModel, order_by="-document_pentru_anul"
        )
        return render(
            request,
            template_name="documente.html",
            context={
                "documente_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
            },
        )

    def post(self, request):

        if request.GET.get("id"):
            # Update
            item = get_object_or_404(DocumenteModel, id=request.GET.get("id"))
            form = DocumenteForm(request.POST, request.FILES, instance=item)
        else:
            # Insert
            form = DocumenteForm(request.POST, request.FILES)

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
                _, page_items = get_page_items(request, DocumenteForm, DocumenteModel)
                return render(
                    request,
                    "documente.html",
                    {
                        "documente_form": form,
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
                " ".join(err),
                extra_tags="🟥 Eroare!",
            )

        return HttpResponseRedirect("/documente/")
