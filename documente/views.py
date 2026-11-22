from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.utils import timezone
from cheltuieli.models import CheltuialaModel
from utils.views import get_page_items, handle_delete_id_query_param
from setari.models import SetariModel
from .forms import DocumenteForm
from .models import (
    DocumenteModel,
    TipDocument,
    DeclaratieTVAModel,
    TipDeclaratieTVA,
    StatusDeclaratieTVA,
    recipisa_parser,
)
from utils.tva import (
    calculeaza_d301,
    calculeaza_d390,
    get_luni_cu_taxare_inversa,
    get_observatii_declaratie,
    termen_depunere,
)
from utils.tva_documente import genereaza_pachet_tva


LUNI_RO_SCURT = {
    1: "Ian", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mai", 6: "Iun",
    7: "Iul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def get_declaratii_tva_context(anul: int):
    """Tabelul pe luni cu declaratiile TVA: TVA de calculat, termen, status."""
    setari = SetariModel.objects.first()
    luni = get_luni_cu_taxare_inversa(anul)
    if not luni:
        return []

    declaratii_existente = {
        (d.tip, d.luna): d
        for d in DeclaratieTVAModel.objects.filter(anul=anul)
    }

    randuri = []
    for luna in luni:
        d301 = calculeaza_d301(anul, luna, setari)
        d390 = calculeaza_d390(anul, luna, setari)
        if not d301:
            continue

        d301_db = declaratii_existente.get((TipDeclaratieTVA.D301.value, luna))
        d390_db = declaratii_existente.get((TipDeclaratieTVA.D390.value, luna))

        randuri.append(
            {
                "luna": luna,
                "luna_nume": LUNI_RO_SCURT[luna],
                "anul": anul,
                "tva_de_plata": d301["total_de_plata"],
                "are_ue": d301["are_ue"],
                "nr_facturi": len({r["nr_doc"] for r in d301["randuri"]}),
                "cif_folosit": d301["cif"],
                "termen": termen_depunere(anul, luna),
                "d301_status": d301_db.status if d301_db else StatusDeclaratieTVA.CALCULATA.value,
                "d390_status": d390_db.status if d390_db else (StatusDeclaratieTVA.CALCULATA.value if d390 else None),
                "observatii": get_observatii_declaratie(anul, luna, setari),
            }
        )
    return randuri


class DocumenteView(View):

    def get(self, request):
        redirect_from_delete = handle_delete_id_query_param(request, DocumenteModel)
        if redirect_from_delete:
            return redirect_from_delete

        form, page_items = get_page_items(
            request, DocumenteForm, DocumenteModel, order_by="-document_pentru_anul"
        )

        anul = request.GET.get("anul_tva")
        anul = int(anul) if anul else timezone.now().year
        # Anii cu operatiuni TVA (pentru selector)
        ani_cu_tva = sorted(
            {
                (c.data_facturii or c.data_inserarii).year
                for c in CheltuialaModel.objects.filter(
                    tip_achizitie__in=["Servicii UE", "Servicii non-UE"],
                    data_inserarii__isnull=False,
                )
            } | {timezone.now().year},
            reverse=True,
        )

        return render(
            request,
            template_name="documente.html",
            context={
                "documente_form": form,
                "page_items": page_items,
                "item_id": request.GET.get("id"),
                "declaratii_tva": get_declaratii_tva_context(anul),
                "anul_tva": anul,
                "ani_cu_tva": ani_cu_tva,
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
            document = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Datele au fost salvate!",
                extra_tags="✅ Succes!",
            )
            # Daca e recipisa D301/D390, o legam de declaratia lunii si marcam Depusa.
            self._leaga_recipisa_de_declaratie(request, document)
        except Exception as err:
            messages.add_message(
                request,
                messages.ERROR,
                " ".join(err) if hasattr(err, "__iter__") else str(err),
                extra_tags="🟥 Eroare!",
            )

        return HttpResponseRedirect("/documente/")

    @staticmethod
    def _leaga_recipisa_de_declaratie(request, document: DocumenteModel):
        if document.tip_document not in (
            TipDocument.DECLARATIE_TVA_DECONT_SPECIAL_301_RECIPISA.value,
            TipDocument.DECLARATIE_TVA_RECAPITULATIVA_390_RECIPISA.value,
        ):
            return
        if not document.fisier.path.endswith(".pdf"):
            return

        recipisa = recipisa_parser(document.fisier.path)
        if not recipisa or not recipisa["anul"] or not recipisa["luna"]:
            return

        declaratie = DeclaratieTVAModel.objects.filter(
            tip=recipisa["tip_declaratie"],
            anul=recipisa["anul"],
            luna=recipisa["luna"],
        ).first()
        if not declaratie:
            return

        declaratie.recipisa = document
        declaratie.status = StatusDeclaratieTVA.DEPUSA
        declaratie.save(update_fields=["recipisa", "status"])

        setari = SetariModel.objects.first()
        if setari and recipisa["cif"] and recipisa["cif"] != declaratie.cif_folosit:
            messages.add_message(
                request,
                messages.WARNING,
                f"CIF-ul din recipisa ({recipisa['cif']}) difera de cel din declaratia generata "
                f"({declaratie.cif_folosit}). Verifica sa nu fi folosit codul normal in locul "
                f"codului special de TVA intracomunitar (sau invers)!",
                extra_tags="⚠️ Atentie!",
            )


class TVAGenereazaView(View):
    """Genereaza intr-un click zip-ul cu D301 + D390 + jurnal + instructiune plata."""

    def get(self, request):
        anul = int(request.GET.get("anul"))
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
            return HttpResponseRedirect("/documente/")

        for tip, snapshot in (
            (TipDeclaratieTVA.D301.value, pachet["d301"]),
            (TipDeclaratieTVA.D390.value, pachet["d390"]),
        ):
            if not snapshot:
                continue
            existenta = DeclaratieTVAModel.objects.filter(
                tip=tip, anul=anul, luna=luna
            ).first()
            # La regenerare pastram statusul avansat (Depusa/Platita) si recipisa;
            # altfel marcam Descarcata.
            status = StatusDeclaratieTVA.DESCARCATA
            if existenta and existenta.status in (
                StatusDeclaratieTVA.DEPUSA, StatusDeclaratieTVA.PLATITA
            ):
                status = existenta.status
            DeclaratieTVAModel.objects.update_or_create(
                tip=tip, anul=anul, luna=luna,
                defaults={
                    "cif_folosit": snapshot["cif"],
                    "total_de_plata": snapshot["total_de_plata"],
                    "randuri": snapshot["randuri"],
                    "status": status,
                },
            )

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


class TVAMarcheazaPlatitaView(View):

    def post(self, request):
        anul = int(request.POST.get("anul"))
        luna = int(request.POST.get("luna"))
        DeclaratieTVAModel.objects.filter(
            tip=TipDeclaratieTVA.D301, anul=anul, luna=luna
        ).update(status=StatusDeclaratieTVA.PLATITA)
        messages.add_message(
            request, messages.SUCCESS,
            f"D301 pentru {luna:02d}/{anul} a fost marcata ca platita.",
            extra_tags="✅ Succes!",
        )
        return HttpResponseRedirect("/documente/")
