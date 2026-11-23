import datetime
import os
import re
import shutil
import zipfile
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from cheltuieli.models import CheltuialaModel
from incasari.models import IncasariModel
from documente.models import DocumenteModel
from facturi.models import FacturaModel
from registre.views import (
    LUNI_RO,
    get_cheltuieli_pe_deductibilitate,
    get_incasari_pe_surse,
    get_registru_de_evidenta_fiscala,
    get_registru_inventar,
    get_registru_jurnal_incasari_si_plati,
    incasari_cheltuieli_dupa_anul_inserarii,
    jurnal_cumparari_dataframe,
    registru_fiscal_dataframe,
    registru_inventar_dataframe,
    registru_jurnal_dataframe,
)
from utils.calcule import calculeaza_taxe_si_impozite
from utils.localitati import lista_localitati
from utils.mijloc_fix_pdf import create_fisa_mijloc_fix_pdf
from utils.pretty_excel import make_excel_pretty
from utils.tva import calculeaza_jurnal_cumparari
from utils.valuta import Valuta
from utils.trezorerie import (
    get_link_iban_trezorerie,
    get_iban_trezorerie_pentru_localitate,
    asigura_date_iban_trezorerie,
    COD_BUGETAR_TVA,
    ANAF_CODURI_IBAN,
)
from .forms import SetariForm
from .models import SetariModel
from core.settings import MEDIA_ROOT, make_media_dir, get_extracts_path


lista_valute = [choice.value for choice in Valuta]


def get_setari_context(form):
    result = SetariModel.objects.first()
    localitate = form.initial.get("localitate") or (result.localitate if result else "")
    return {
        "setari_form": form,
        "lista_localitati": lista_localitati,
        "lista_valute": lista_valute,
        "link_iban_trezorerie": get_link_iban_trezorerie(localitate),
        "cod_bugetar_tva": COD_BUGETAR_TVA,
        "ani_export": get_ani_export(),
        "anul_curent": timezone.now().year,
    }


def get_ani_export():
    """Anii pentru care exista date in aplicatie (incasari, cheltuieli,
    documente), pentru selectorul de an la exportul datelor."""
    current_year = timezone.now().year
    ani = {current_year}

    for model, camp in (
        (IncasariModel, "data_inserarii"),
        (CheltuialaModel, "data_inserarii"),
    ):
        dates = model.objects.filter(**{f"{camp}__isnull": False}).values_list(camp, flat=True)
        ani.update(d.year for d in dates if d)

    ani.update(
        an for an in DocumenteModel.objects.values_list("document_pentru_anul", flat=True) if an
    )
    ani.update(
        d.year for d in DocumenteModel.objects.values_list("actualizat_la", flat=True) if d
    )

    return sorted(ani, reverse=True)


class SetariIbanTrezorerieView(View):
    """Cand utilizatorul selecteaza localitatea, intoarce IBAN-ul trezoreriei
    pentru plata TVA (extras din sursele oficiale ANAF) + linkul de verificare."""

    def get(self, request):
        localitate = request.GET.get("localitate", "")
        potrivire = get_iban_trezorerie_pentru_localitate(localitate)
        return JsonResponse({
            "iban": potrivire["iban"] if potrivire else None,
            "nume_trezorerie": potrivire["nume_trezorerie"] if potrivire else None,
            "sursa": potrivire["sursa"] if potrivire else get_link_iban_trezorerie(localitate),
            "pagina_anaf": ANAF_CODURI_IBAN,
            "cod_bugetar": COD_BUGETAR_TVA,
        })


class SetariView(View):

    def get(self, request):
        result = SetariModel.objects.first()
        form = SetariForm(instance=result)
        return render(
            request,
            template_name="setari.html",
            context=get_setari_context(form),
        )

    def post(self, request, *args, **kwargs):
        form = SetariForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                "setari.html",
                context=get_setari_context(form),
            )

        setari = form.save(commit=False)

        # Daca IBAN-ul trezoreriei nu a fost completat (utilizatorul a salvat
        # fara sa selecteze din nou localitatea), il deducem automat din
        # localitate, din tabelul extras din sursele oficiale ANAF.
        if not setari.cont_iban_trezoreria:
            # Daca tabelul iban_trezorerie.json lipseste, il descarcam acum
            # de pe ANAF (o singura data; apoi ramane salvat local).
            if not asigura_date_iban_trezorerie():
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Nu am putut descarca lista IBAN-urilor trezoreriilor de pe ANAF "
                    "(lipsa conexiune?). Completeaza IBAN-ul trezoreriei manual din "
                    "lista ANAF, sau salveaza din nou cand ai conexiune la internet.",
                    extra_tags="⚠️ Atentie!",
                )
            potrivire = get_iban_trezorerie_pentru_localitate(setari.localitate)
            if potrivire:
                setari.cont_iban_trezoreria = potrivire["iban"]

        SetariModel.objects.all().delete()

        setari.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return redirect("/setari/")



class SetariViewDownloadData(View):
    """Exportul datelor pentru un an selectat de utilizator.

    Structura zip-ului:
    - documente/  -> fisierele urcate in pagina Documente pentru anul selectat;
    - cheltuieli/ -> documentele justificative ale cheltuielilor din anul selectat;
    - incasari/   -> documentele justificative ale incasarilor din anul selectat;
    - in root: registrele anului in format .xlsx (Registrul Jurnal, Registrul
      Inventar, Registrul Fiscal, Jurnalul de cumparari), fisele mijloacelor fixe
      in folderul fise_mijloace_fixe/ si SUMAR.html cu metricile anului.

    Exportul se face pe un singur an ca sa nu blocam aplicatia procesand
    toate datele dintr-o data.
    """

    def post(self, request):

        anul = request.POST.get("anul")
        try:
            anul = int(anul) if anul else timezone.now().year
        except (TypeError, ValueError):
            anul = timezone.now().year

        extracts_path = get_extracts_path("export_date")

        incasari, cheltuieli = incasari_cheltuieli_dupa_anul_inserarii(anul)
        incasari = list(incasari.order_by("data_inserarii", "id"))
        cheltuieli = list(cheltuieli.order_by("data_inserarii", "id"))

        # Documentele urcate in pagina Documente pentru anul selectat
        # (document_pentru_anul, cu fallback pe anul urcarii).
        documente = list(
            DocumenteModel.objects.filter(
                Q(document_pentru_anul=anul)
                | Q(document_pentru_anul__isnull=True, actualizat_la__year=anul)
            ).order_by("id")
        )

        def adauga_fisier_in_zip(zipf, filefield, folder, nume_alternativ=None):
            """Scrie un fisier urcat in aplicatie in folderul dat din zip.
            Daca fisierul lipseste de pe disc, se sare peste el (nu blocam exportul)."""
            if not filefield:
                return
            try:
                fp = filefield.path
                if not os.path.isfile(fp):
                    return
                nume = nume_alternativ or os.path.basename(fp)
                zipf.write(fp, f"{folder}/{nume}")
            except (ValueError, OSError):
                pass

        # --- Registrele anului (xlsx) ---
        fisiere_registre = []

        def salveaza_xlsx(df, nume_fisier):
            fp = os.path.join(extracts_path, nume_fisier)
            df.to_excel(fp, index=False)
            make_excel_pretty(fp)
            fisiere_registre.append(fp)

        rjip_data = get_registru_jurnal_incasari_si_plati(
            request, incasari, cheltuieli, anul=anul
        )
        if rjip_data:
            salveaza_xlsx(
                registru_jurnal_dataframe(rjip_data),
                f"Registru_Jurnal_{anul}.xlsx",
            )

        total_incasari_brut = IncasariModel.get_total_incasari(anul)
        total_cheltuieli = CheltuialaModel.get_total_cheltuieli(anul)
        total_incasari_net = round(total_incasari_brut - total_cheltuieli, 2)

        ref_data = get_registru_de_evidenta_fiscala(
            request, total_incasari_brut, total_incasari_net, total_cheltuieli, anul=anul
        )
        salveaza_xlsx(registru_fiscal_dataframe(ref_data), f"Registru_Fiscal_{anul}.xlsx")

        # Registrul-inventar: obiectele de inventar si mijloacele fixe active
        # (nu doar cele cumparate in anul selectat - inventarul e cumulativ).
        inventar_data = get_registru_inventar(dbid=True)
        fise_mijloace_fixe = []
        for item in inventar_data:
            if item["mijloc_fix"]:
                try:
                    fisa_pdf = create_fisa_mijloc_fix_pdf(
                        item["db_id"], item["nr_crt"], doar_pdf=True
                    )
                    item["fisier"] = os.path.basename(fisa_pdf)
                    fise_mijloace_fixe.append(fisa_pdf)
                except (ValueError, OSError):
                    # Fisierul justificativ lipseste de pe disc: pastram
                    # registrul, dar sarim peste fisa acestui mijloc fix.
                    item["fisier"] = os.path.basename(item["fisier"])
            else:
                item["fisier"] = os.path.basename(item["fisier"])

        if inventar_data:
            salveaza_xlsx(
                registru_inventar_dataframe(inventar_data),
                f"Registru_Inventar_{anul}.xlsx",
            )

        jurnal_cumparari = calculeaza_jurnal_cumparari(anul)
        if jurnal_cumparari:
            salveaza_xlsx(
                jurnal_cumparari_dataframe(jurnal_cumparari),
                f"Jurnal_Cumparaturi_{anul}.xlsx",
            )

        # --- SUMAR.html cu metricile anului ---
        sumar = self.genereaza_sumar(
            anul, incasari, cheltuieli, documente,
            total_incasari_brut, total_cheltuieli, total_incasari_net,
            jurnal_cumparari,
        )
        sumar_fp = os.path.join(extracts_path, "SUMAR.html")
        with open(sumar_fp, "w", encoding="utf-8") as f:
            f.write(sumar)

        # --- Zip-ul final ---
        zip_filename = os.path.join(get_extracts_path(), f"export_date_{anul}.zip")
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for doc in documente:
                adauga_fisier_in_zip(zipf, doc.fisier, "documente")

            for cheltuiala in cheltuieli:
                adauga_fisier_in_zip(zipf, cheltuiala.fisier, "cheltuieli")
                adauga_fisier_in_zip(
                    zipf, cheltuiala.document_justificativ_iesire_din_uz, "cheltuieli"
                )

            for incasare in incasari:
                adauga_fisier_in_zip(zipf, incasare.fisier, "incasari")
                # PDF-ul/XML-ul facturilor emise din aplicatie, atasate incasarii.
                factura = getattr(incasare, "factura", None)
                if factura:
                    adauga_fisier_in_zip(zipf, factura.fisier_factura_pdf, "incasari")
                    adauga_fisier_in_zip(zipf, factura.fisier_efactura_xml, "incasari")

            for fp in fisiere_registre:
                zipf.write(fp, os.path.basename(fp))
            for fp in fise_mijloace_fixe:
                zipf.write(fp, f"fise_mijloace_fixe/{os.path.basename(fp)}")
            zipf.write(sumar_fp, "SUMAR.html")

        with open(zip_filename, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/zip")
            response["Content-Disposition"] = (
                f"attachment; filename={os.path.basename(zip_filename)}"
            )
            return response

    @staticmethod
    def genereaza_sumar(
        anul, incasari, cheltuieli, documente,
        total_incasari_brut, total_cheltuieli, total_incasari_net,
        jurnal_cumparari,
    ):
        """Metricile anului, ca pagina HTML standalone (SUMAR.html din zip-ul
        de export), cu PicoCSS incarcate de pe CDN - se deschide in orice
        browser, cu conexiune la internet."""

        fmt = lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        setari = SetariModel.objects.first()
        if setari:
            la_stat = calculeaza_taxe_si_impozite(
                max(total_incasari_net, 0), anul,
                setari.scutit_cas, setari.scutit_cass, setari.scutit_impozit,
            )
        else:
            la_stat = calculeaza_taxe_si_impozite(max(total_incasari_net, 0), anul)

        total_neincasate = IncasariModel.get_total_neincasate(anul)

        # Pentru anul curent media se calculeaza pe lunile trecute, nu pe 12.
        today = timezone.now().date()
        luni = today.month if anul == today.year else 12
        venit_net_dupa_taxe = round(total_incasari_net - la_stat["total_taxe_impozite"], 2)

        incasari_pe_luni = IncasariModel.get_total_incasari_pe_luni(anul)
        cheltuieli_pe_luni = CheltuialaModel.get_total_cheltuieli_pe_luni(anul)

        cea_mai_mare_incasare = max(incasari, key=lambda i: i.suma_in_ron or 0, default=None)
        cea_mai_mare_cheltuiala = max(cheltuieli, key=lambda c: c.suma_in_ron or 0, default=None)

        # Plati la stat deja facute in anul selectat (dovezi de plata urcate
        # in pagina Documente, cu suma extrasa automat din PDF).
        plati_la_stat_an = 0
        for doc in documente:
            if doc.tip_document == "Dovada plata taxe si impozite" and doc.mentiuni:
                match = re.search(r"Plata spv ([\d.,]+) RON", doc.mentiuni)
                if match:
                    try:
                        plati_la_stat_an += float(match.group(1).replace(",", "."))
                    except ValueError:
                        pass
        plati_la_stat_an = round(plati_la_stat_an, 2)
        rest_de_plata = round(la_stat["total_taxe_impozite"] - plati_la_stat_an, 2)

        taxe = [
            ("CAS (pensie 25%)", fmt(la_stat["cas_pensie"])),
            ("CASS (sanatate 10%)", fmt(la_stat["cass_sanatate"])),
            ("Impozit pe venit (10%)", fmt(la_stat["impozit_pe_venit"])),
            ("Total de platit", fmt(la_stat["total_taxe_impozite"])),
            (f"Deja platit in {anul} (dovezi de plata urcate)", fmt(plati_la_stat_an)),
            ("Rest de plata estimat", fmt(rest_de_plata)),
        ]
        if jurnal_cumparari:
            taxe.append(
                ("TVA autolichidata (taxare inversa, D301)", fmt(jurnal_cumparari["total_tva"]))
            )

        context = {
            "anul": anul,
            "an_curent": anul == today.year,
            "generat_la": timezone.now().strftime("%d.%m.%Y %H:%M"),
            "total_incasari_brut": fmt(total_incasari_brut),
            "total_cheltuieli": fmt(total_cheltuieli),
            "total_incasari_net": fmt(total_incasari_net),
            "venit_net_dupa_taxe": fmt(venit_net_dupa_taxe),
            "la_stat": {k: fmt(v) for k, v in la_stat.items()},
            "incasari_cheltuieli": [
                ("Total incasari (brut)", fmt(total_incasari_brut)),
                ("Total cheltuieli deductibile (inclusiv amortizari)", fmt(total_cheltuieli)),
                ("Venit net (inainte de taxe)", fmt(total_incasari_net)),
                ("Total taxe si impozite estimate", fmt(la_stat["total_taxe_impozite"])),
                ("Venit net dupa taxe", fmt(venit_net_dupa_taxe)),
                ("Facturi neincasate", fmt(total_neincasate)),
                ("Numar incasari inregistrate", len(incasari)),
                ("Numar cheltuieli inregistrate", len(cheltuieli)),
                ("Numar documente urcate", len(documente)),
            ],
            "luni": luni,
            "medii_lunare": [
                ("Incasari medii pe luna", fmt(total_incasari_brut / luni)),
                ("Cheltuieli medii pe luna", fmt(total_cheltuieli / luni)),
                ("Venit net mediu pe luna (dupa taxe)", fmt(venit_net_dupa_taxe / luni)),
                ("Taxe si impozite medii pe luna", fmt(la_stat["total_taxe_impozite"] / luni)),
            ],
            "taxe": taxe,
            "tva_autolichidata": bool(jurnal_cumparari),
            "cea_mai_mare_incasare": {
                "suma": fmt(cea_mai_mare_incasare.suma_in_ron),
                "data": cea_mai_mare_incasare.data_inserarii.isoformat(),
                "detalii": cea_mai_mare_incasare.sursa_venit,
            } if cea_mai_mare_incasare else None,
            "cea_mai_mare_cheltuiala": {
                "suma": fmt(cea_mai_mare_cheltuiala.suma_in_ron),
                "data": cea_mai_mare_cheltuiala.data_inserarii.isoformat(),
                "detalii": cea_mai_mare_cheltuiala.nume_cheltuiala,
            } if cea_mai_mare_cheltuiala else None,
            "incasari_pe_surse": [
                {"nume": i["nume"], "valoare": fmt(i["valoare"])}
                for i in get_incasari_pe_surse(anul)
            ],
            "cheltuieli_pe_deductibilitate": [
                {"nume": i["nume"], "valoare": fmt(i["valoare"])}
                for i in get_cheltuieli_pe_deductibilitate(anul)
            ],
            "pe_luni": [
                {
                    "luna": LUNI_RO[luna],
                    "incasari": fmt(incasari_pe_luni[luna - 1]),
                    "cheltuieli": fmt(cheltuieli_pe_luni[luna - 1]),
                }
                for luna in range(1, 13)
            ],
            "amortizari": SetariViewDownloadData._tabele_amortizare(anul, fmt),
        }

        html = render_to_string("sumar.html", context)

        return html

    @staticmethod
    def _tabele_amortizare(anul, fmt):
        """Tabel de amortizare per mijloc fix activ (An, Luna, Suma RON), de la
        inceputul amortizarii pana la amortizarea completa - cat se poate deduce
        in fiecare luna. Lunile viitoare sunt estimate."""
        mijloace_fixe = [
            mf for mf in CheltuialaModel.objects.filter(mijloc_fix=True, scos_din_uz=False)
            .order_by("data_inceperii_amortizarii", "id")
            if mf.data_inceperii_amortizarii and mf.data_amortizarii_complete
            and mf.amortizare_lunara
            and mf.data_amortizarii_complete.year >= anul
        ]

        today = timezone.now().date()
        tabele = []
        for mf in mijloace_fixe:
            inceput = mf.data_inceperii_amortizarii.replace(day=1)
            sfarsit = mf.data_amortizarii_complete.replace(day=1)

            randuri = []
            total = 0
            cursor = inceput
            while cursor <= sfarsit:
                randuri.append({
                    "an": cursor.year,
                    "luna": LUNI_RO[cursor.month],
                    "suma": fmt(mf.amortizare_lunara),
                    "estimat": cursor > today.replace(day=1),
                })
                total += mf.amortizare_lunara
                # luna urmatoare
                cursor = (
                    datetime.date(cursor.year + 1, 1, 1)
                    if cursor.month == 12
                    else datetime.date(cursor.year, cursor.month + 1, 1)
                )

            tabele.append({
                "nume": mf.nume_cheltuiala,
                "valoare": fmt(mf.suma_in_ron),
                "amortizare_lunara": fmt(mf.amortizare_lunara),
                "perioada": f"{LUNI_RO[inceput.month]} {inceput.year} - {LUNI_RO[sfarsit.month]} {sfarsit.year}",
                "ani": mf.ani_amortizare,
                "randuri": randuri,
                "total": fmt(total),
            })

        return tabele


class SetariViewDropData(View):

    def post(self, request):

        SetariModel.objects.all().delete()
        CheltuialaModel.objects.all().delete()
        IncasariModel.objects.all().delete()
        DocumenteModel.objects.all().delete()
        FacturaModel.objects.all().delete()

        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        make_media_dir()

        return redirect("/setari/")
