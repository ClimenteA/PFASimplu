import datetime
import logging
import os
import shutil
import zipfile

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import HttpResponse, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View

from cheltuieli.calcul import q_mijloc_fix, q_scos_din_uz
from cheltuieli.models import CheltuialaModel
from core.settings import (
    APP_VERSION,
    GITHUB_REPO_URL,
    get_extracts_path,
    get_media_path,
    make_media_dir,
)
from documente.models import DocumenteModel, TipDocument
from facturi.models import FacturaModel
from incasari.models import IncasariModel
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
from utils.actualizare import (
    EroareActualizare,
    este_standalone,
    pregateste_actualizarea,
)
from utils.calcule import calculeaza_taxe_si_impozite
from utils.decimale import D, rotund2
from utils.github_data import get_latest_app_version
from utils.localitati import lista_localitati
from utils.mijloc_fix_pdf import create_fisa_mijloc_fix_pdf
from utils.pretty_excel import make_excel_pretty
from utils.trezorerie import (
    ANAF_CODURI_IBAN,
    COD_BUGETAR_TVA,
    asigura_date_iban_trezorerie,
    get_iban_trezorerie_pentru_localitate,
    get_link_iban_trezorerie,
)
from utils.tva import calculeaza_jurnal_cumparari
from utils.valuta import Valuta
from utils.views import pregateste_df_export

from .forms import SetariForm
from .models import McpApiKey, SetariModel

lista_valute = [choice.value for choice in Valuta]
logger = logging.getLogger(__name__)


def _este_versiune_mai_noua(remote: str, local: str) -> bool:
    """Compara versiunile semver (ex. '2.0.7' vs '3.0.0') ca tuple de intregi,
    ca '10.0.0' sa fie considerat mai nou decat '9.0.0'."""
    if not remote or not local or remote == local:
        return False
    try:
        return tuple(map(int, remote.split("."))) > tuple(map(int, local.split(".")))
    except ValueError:
        return False


def get_setari_context(form, request):
    result = SetariModel.objects.first()
    localitate = form.initial.get("localitate") or (result.localitate if result else "")
    latest_app_version = get_latest_app_version()
    context = {
        "setari_form": form,
        "lista_localitati": lista_localitati,
        "lista_valute": lista_valute,
        "link_iban_trezorerie": get_link_iban_trezorerie(localitate),
        "cod_bugetar_tva": COD_BUGETAR_TVA,
        "ani_export": get_ani_export(),
        "anul_curent": timezone.now().year,
        "app_version": APP_VERSION,
        "latest_app_version": latest_app_version,
        "repo_url": GITHUB_REPO_URL,
        "update_available": _este_versiune_mai_noua(latest_app_version, APP_VERSION),
        "poate_actualiza": este_standalone(),
        "mcp_key": McpApiKey.objects.filter(user=request.user).first(),
        "mcp_key_once": None,
    }
    # Cheia in clar e afisata o singura data, imediat dupa generare, si apoi
    # stearsa din sesiune (nu ramane in istoric/URL/logs).
    context["mcp_key_once"] = request.session.pop("mcp_key_once", None)
    return context


def get_ani_export():
    """Anii pentru care exista date in aplicatie (incasari, cheltuieli,
    documente), pentru selectorul de an la exportul datelor."""
    current_year = timezone.now().year
    ani = {current_year}

    for model, camp in (
        (IncasariModel, "data_inserarii"),
        (CheltuialaModel, "data_inserarii"),
    ):
        dates = model.objects.filter(**{f"{camp}__isnull": False}).values_list(
            camp, flat=True
        )
        ani.update(d.year for d in dates if d)

    ani.update(
        d.year
        for d in DocumenteModel.objects.values_list("data_document", flat=True)
        if d
    )
    ani.update(
        d.year
        for d in DocumenteModel.objects.values_list("actualizat_la", flat=True)
        if d
    )

    return sorted(ani, reverse=True)


class SetariIbanTrezorerieView(View):
    """Cand utilizatorul selecteaza localitatea, intoarce IBAN-ul trezoreriei
    pentru plata TVA (extras din sursele oficiale ANAF) + linkul de verificare."""

    def get(self, request):
        localitate = request.GET.get("localitate", "")
        potrivire = get_iban_trezorerie_pentru_localitate(localitate)
        return JsonResponse(
            {
                "iban": potrivire["iban"] if potrivire else None,
                "nume_trezorerie": potrivire["nume_trezorerie"] if potrivire else None,
                "sursa": potrivire["sursa"]
                if potrivire
                else get_link_iban_trezorerie(localitate),
                "pagina_anaf": ANAF_CODURI_IBAN,
                "cod_bugetar": COD_BUGETAR_TVA,
            }
        )


class SetariView(View):
    def get(self, request):
        result = SetariModel.objects.first()
        form = SetariForm(instance=result)
        return render(
            request,
            template_name="setari.html",
            context=get_setari_context(form, request),
        )

    def post(self, request, *args, **kwargs):
        # Exista un singur set de setari per utilizator; il actualizam, nu il
        # stergem si resalvam (vecheaImplementare pierdea ID-ul si fisierele).
        form = SetariForm(request.POST, instance=SetariModel.objects.first())

        if not form.is_valid():
            return render(
                request,
                "setari.html",
                context=get_setari_context(form, request),
            )

        setari = form.instance

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

        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Datele au fost salvate!",
            extra_tags="✅ Succes!",
        )
        return redirect("/setari/")


class SetariActualizeazaView(View):
    """Instaleaza executabilul nou, numai la cererea utilizatorului."""

    def post(self, request):
        versiune = get_latest_app_version()
        if not versiune or not _este_versiune_mai_noua(versiune, APP_VERSION):
            messages.add_message(
                request,
                messages.ERROR,
                "Nu exista o versiune noua de instalat.",
                extra_tags="🟥 Eroare!",
            )
            return redirect("/setari/")

        try:
            mesaj = pregateste_actualizarea(versiune)
        except EroareActualizare as exc:
            logger.warning("Actualizare esuata: %s", exc)
            messages.add_message(
                request, messages.ERROR, str(exc), extra_tags="🟥 Eroare!"
            )
            return redirect("/setari/")

        messages.add_message(request, messages.SUCCESS, mesaj, extra_tags="✅ Succes!")
        return redirect("/setari/")


class SetariMcpKeyGenerateView(View):
    """Genereaza (sau roteste) cheia folosita de serverul MCP.
    Cheia in clar ajunge doar in sesiune, ca sa fie afisata o singura data."""

    def post(self, request):
        _, key = McpApiKey.generate(request.user)
        # Cheia e afisata direct in campul password de pe pagina Setari;
        # un mesaj-modal ar acoperi butonul de copiat chiar cand e nevoie de el.
        request.session["mcp_key_once"] = key
        # Anchorul face pagina sa se deschida direct la sectiunea MCP.
        return redirect("/setari/#cheie-mcp")


class SetariMcpKeyRevokeView(View):
    """Revoca definitiv cheia MCP curenta."""

    def post(self, request):
        McpApiKey.revoke(request.user)
        request.session.pop("mcp_key_once", None)
        # Fara mesaj-modal: vrem ca sectiunea MCP sa fie vizibila dupa scroll.
        return redirect("/setari/#cheie-mcp")


class SetariViewDownloadData(View):
    """Exportul datelor pentru un an selectat de utilizator.

    Structura zip-ului:
    - documente/  -> fisierele urcate in pagina Documente pentru anul selectat;
    - cheltuieli/ -> documentele justificative ale cheltuielilor din anul selectat;
    - incasari/   -> documentele justificative ale incasarilor din anul selectat;
    - in root: registrele anului in format .xlsx (Registrul Jurnal, Registrul
      Inventar, Registrul Fiscal, Jurnalul de cumparari), fisele mijloacelor fixe
      in folderul fise_mijloace_fixe/ si SUMAR.html cu metricile anului, inclusiv
      ultima serie si numar de factura emisa.

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
                Q(data_document__year=anul)
                | Q(data_document__isnull=True, actualizat_la__year=anul)
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
            pregateste_df_export(df).to_excel(fp, index=False)
            make_excel_pretty(fp, number_format="General")
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
        total_incasari_net = rotund2(D(total_incasari_brut) - D(total_cheltuieli))

        ref_data = get_registru_de_evidenta_fiscala(
            request,
            total_incasari_brut,
            total_incasari_net,
            total_cheltuieli,
            anul=anul,
        )
        salveaza_xlsx(
            registru_fiscal_dataframe(ref_data), f"Registru_Fiscal_{anul}.xlsx"
        )

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
            anul,
            incasari,
            cheltuieli,
            documente,
            total_incasari_brut,
            total_cheltuieli,
            total_incasari_net,
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
        anul,
        incasari,
        cheltuieli,
        documente,
        total_incasari_brut,
        total_cheltuieli,
        total_incasari_net,
        jurnal_cumparari,
    ):
        """Metricile anului, ca pagina HTML standalone (SUMAR.html din zip-ul
        de export), cu PicoCSS incarcate de pe CDN - se deschide in orice
        browser, cu conexiune la internet."""

        fmt = lambda v: (
            f"{rotund2(D(v)):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        setari = SetariModel.objects.first()
        if setari:
            la_stat = calculeaza_taxe_si_impozite(
                max(total_incasari_net, 0),
                anul,
                setari.scutit_cas,
                setari.scutit_cass,
                setari.scutit_impozit,
            )
        else:
            la_stat = calculeaza_taxe_si_impozite(max(total_incasari_net, 0), anul)

        total_neincasate = IncasariModel.get_total_neincasate(anul)

        # Ultima factura emisa (serie + numar), atat in anul exportat cat si
        # in aplicatie - informatia e utila in arhiva de sfarsit de an pentru
        # a stii de unde se continua numerotarea.
        def date_ultima_factura(factura):
            if not factura:
                return None
            return {
                "serie": factura.serie,
                "numar": factura.numar,
                "serie_numar": f"{factura.serie}-{factura.numar}",
                "data_emitere": factura.data_emitere.isoformat(),
                "total_de_plata": fmt(factura.total_de_plata),
            }

        ultima_factura_an = date_ultima_factura(
            FacturaModel.objects.filter(
                Q(data_emitere__year=anul) | Q(data_inserarii__year=anul)
            )
            .order_by("-data_emitere", "-id")
            .first()
        )
        ultima_factura = date_ultima_factura(
            FacturaModel.objects.order_by("-data_emitere", "-id").first()
        )

        # Pentru anul curent media se calculeaza pe lunile trecute, nu pe 12.
        today = timezone.now().date()
        luni = today.month if anul == today.year else 12
        venit_net_dupa_taxe = rotund2(
            D(total_incasari_net) - D(la_stat["total_taxe_impozite"])
        )

        incasari_pe_luni = IncasariModel.get_total_incasari_pe_luni(anul)
        cheltuieli_pe_luni = CheltuialaModel.get_total_cheltuieli_pe_luni(anul)

        cea_mai_mare_incasare = max(
            incasari, key=lambda i: i.suma_in_ron or 0, default=None
        )
        cea_mai_mare_cheltuiala = max(
            cheltuieli, key=lambda c: c.suma_in_ron or 0, default=None
        )

        # Plati la stat deja facute in anul selectat (dovezi de plata urcate
        # in pagina Documente, cu suma extrasa automat din PDF).
        plati_la_stat_an = rotund2(
            sum(
                (
                    D(doc.suma_plata)
                    for doc in documente
                    if doc.tip_document
                    == TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE.value
                ),
                D(0),
            )
        )
        rest_de_plata = rotund2(D(la_stat["total_taxe_impozite"]) - plati_la_stat_an)

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
                (
                    "TVA autolichidata (taxare inversa, D301)",
                    fmt(jurnal_cumparari["total_tva"]),
                )
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
            "ultima_factura": ultima_factura,
            "ultima_factura_an": ultima_factura_an,
            "incasari_cheltuieli": [
                ("Total incasari (brut)", fmt(total_incasari_brut)),
                (
                    "Total cheltuieli deductibile (inclusiv amortizari)",
                    fmt(total_cheltuieli),
                ),
                ("Venit net (inainte de taxe)", fmt(total_incasari_net)),
                (
                    "Total taxe si impozite estimate",
                    fmt(la_stat["total_taxe_impozite"]),
                ),
                ("Venit net dupa taxe", fmt(venit_net_dupa_taxe)),
                ("Facturi neincasate", fmt(total_neincasate)),
                ("Numar incasari inregistrate", len(incasari)),
                ("Numar cheltuieli inregistrate", len(cheltuieli)),
                ("Numar documente urcate", len(documente)),
            ],
            "luni": luni,
            "medii_lunare": [
                (
                    "Incasari medii pe luna",
                    fmt(rotund2(D(total_incasari_brut) / D(luni))),
                ),
                (
                    "Cheltuieli medii pe luna",
                    fmt(rotund2(D(total_cheltuieli) / D(luni))),
                ),
                (
                    "Venit net mediu pe luna (dupa taxe)",
                    fmt(rotund2(D(venit_net_dupa_taxe) / D(luni))),
                ),
                (
                    "Taxe si impozite medii pe luna",
                    fmt(rotund2(D(la_stat["total_taxe_impozite"]) / D(luni))),
                ),
            ],
            "taxe": taxe,
            "tva_autolichidata": bool(jurnal_cumparari),
            "cea_mai_mare_incasare": {
                "suma": fmt(cea_mai_mare_incasare.suma_in_ron),
                "data": cea_mai_mare_incasare.data_inserarii.isoformat(),
                "detalii": cea_mai_mare_incasare.sursa_venit,
            }
            if cea_mai_mare_incasare
            else None,
            "cea_mai_mare_cheltuiala": {
                "suma": fmt(cea_mai_mare_cheltuiala.suma_in_ron),
                "data": cea_mai_mare_cheltuiala.data_inserarii.isoformat(),
                "detalii": cea_mai_mare_cheltuiala.nume_cheltuiala,
            }
            if cea_mai_mare_cheltuiala
            else None,
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
            mf
            for mf in CheltuialaModel.objects.filter(q_mijloc_fix()).exclude(
                q_scos_din_uz()
            )
            if mf.data_inceperii_amortizarii
            and mf.data_amortizarii_complete
            and mf.amortizare_lunara
            and mf.data_amortizarii_complete.year >= anul
        ]
        mijloace_fixe.sort(key=lambda mf: (mf.data_inceperii_amortizarii, mf.id))

        today = timezone.now().date()
        tabele = []
        for mf in mijloace_fixe:
            inceput = mf.data_inceperii_amortizarii.replace(day=1)
            sfarsit = mf.data_amortizarii_complete.replace(day=1)

            randuri = []
            total = D(0)
            cursor = inceput
            while cursor <= sfarsit:
                randuri.append(
                    {
                        "an": cursor.year,
                        "luna": LUNI_RO[cursor.month],
                        "suma": fmt(mf.amortizare_lunara),
                        "estimat": cursor > today.replace(day=1),
                    }
                )
                total += D(mf.amortizare_lunara)
                # luna urmatoare
                cursor = (
                    datetime.date(cursor.year + 1, 1, 1)
                    if cursor.month == 12
                    else datetime.date(cursor.year, cursor.month + 1, 1)
                )

            tabele.append(
                {
                    "nume": mf.nume_cheltuiala,
                    "valoare": fmt(mf.suma_in_ron),
                    "amortizare_lunara": fmt(mf.amortizare_lunara),
                    "perioada": f"{LUNI_RO[inceput.month]} {inceput.year} - {LUNI_RO[sfarsit.month]} {sfarsit.year}",
                    "ani": mf.ani_amortizare,
                    "randuri": randuri,
                    "total": fmt(total),
                }
            )

        return tabele


class SetariViewDropData(View):
    def post(self, request):

        SetariModel.objects.all().delete()
        CheltuialaModel.objects.all().delete()
        IncasariModel.objects.all().delete()
        DocumenteModel.objects.all().delete()
        FacturaModel.objects.all().delete()

        # In modul multi-user se sterge doar folderul media al utilizatorului
        # curent, nu si datele celorlalti utilizatori.
        shutil.rmtree(get_media_path(), ignore_errors=True)
        make_media_dir()

        return redirect("/setari/")
