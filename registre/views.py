import os
import shutil
import itertools
from copy import copy
import pandas as pd
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Sum, Q
from cheltuieli.models import CheltuialaModel, Deductibilitate
from incasari.models import IncasariModel, SursaVenit
from documente.models import DocumenteModel
from utils.calcule import calculeaza_taxe_si_impozite
from utils.valuta import ron_to_eur
from utils.views import download_csv_or_xlsx
from core.settings import MEDIA_ROOT, get_extracts_path
from zipfile import ZipFile
from utils.pretty_excel import make_excel_pretty
from utils.mijloc_fix_pdf import create_fisa_mijloc_fix_pdf
from utils.github_data import new_version_available


import matplotlib
# prevent thread issue with flaskwebgui
matplotlib.use("SVG") 

import matplotlib.pyplot as plt


class RegistruJurnalDescarcaView(View):

    def get(self, request):
        filetype = request.GET.get("filetype").lower()
        anul = get_year_from_request(request)
        incasari, cheltuieli = incasari_cheltuieli_dupa_anul_inserarii(anul)
        data = get_registru_jurnal_incasari_si_plati(request, incasari, cheltuieli)

        if not data:
            return redirect("/registre/")
        
        file_ids = list(set([d["documentId"] for d in data if d["documentId"] is not None]))

        query = Q()
        for file_id in file_ids:
            query |= Q(fisier__startswith=file_id)

        incasari_fisiere = incasari.filter(query)
        cheltuieli_fisiere = cheltuieli.filter(query)

        rjip_files_path = get_extracts_path("rjip")
        
        rjip_files = []
        for item in incasari_fisiere:
            fp = shutil.copy2(item.fisier.path, os.path.join(rjip_files_path, os.path.basename(item.fisier.path))) 
            rjip_files.append(fp)

        for item in cheltuieli_fisiere:
            fp = shutil.copy2(item.fisier.path, os.path.join(rjip_files_path, os.path.basename(item.fisier.path))) 
            rjip_files.append(fp)

        df = pd.DataFrame(data)
        df = df.drop(columns=["end_of_month", "documentId"])
        df = df.rename(
            columns={
                "nr_crt": "Nr.Crt.",
                "data": "Data",
                "documentul": "Documentul (fel, numar)",
                "felul_operatiunii": "Felul operatiunii (explicatii)",
                "incasari_numerar": "Incasari Numerar",
                "incasari_banca": "Incasari Banca",
                "plati_numerar": "Plati Numerar",
                "plati_banca": "Plati Banca",
            }
        )
        
        extracts_path = get_extracts_path()

        if filetype == "xlsx":
            rjip_fp = os.path.join(extracts_path, "registru_jurnal_incasari_si_plati.xlsx")
            df.to_excel(rjip_fp, index=False)
            make_excel_pretty(rjip_fp)
        elif filetype == "csv":
            rjip_fp = os.path.join(extracts_path, "registru_jurnal_incasari_si_plati.csv")
            df.to_csv(rjip_fp, index=False)
        else:
            return redirect("/registre/")
        

        zip_filename = os.path.join(extracts_path, f"registru_jurnal_{anul}.zip")
        with ZipFile(zip_filename, "w") as zipf:
            for file in rjip_files:
                zipf.write(file, os.path.join("documente", os.path.basename(file)))
            zipf.write(rjip_fp, os.path.basename(rjip_fp))
            
        response = HttpResponse(
            open(zip_filename, "rb"), content_type="application/zip"
        )
        response["Content-Disposition"] = (
            f"attachment; filename={os.path.basename(zip_filename)}"
        )
        return response


class RegistruFiscalDescarcaView(View):

    def get(self, request):
        overview_data = get_cards_and_charts_data(request)
        data = get_registru_de_evidenta_fiscala(
            request,
            overview_data["total_incasari_brut"],
            overview_data["total_incasari_net"],
            overview_data["total_cheltuieli"],
        )
        df = pd.DataFrame(data)

        df = df.rename(
            columns={
                "nr_crt": "Nr.Crt.",
                "elemente_de_calcul": "Elemente de calcul pentru stabilirea venitului net annual/pierderii nete anuale",
                "valoare": "Valoare",
                "anul": "Anul",
            }
        )

        return download_csv_or_xlsx(request, df, "registrul_de_evidenta_fiscala")


class RegistruInventarDescarcaView(View):

    def get(self, request):
        filetype = request.GET.get("filetype").lower()
        data = get_registru_inventar(dbid=True)
        
        src_filepaths = []
        for item in data:
            if item["mijloc_fix"]:
                zip_filepath = create_fisa_mijloc_fix_pdf(item['db_id'], item['nr_crt'])
                item["fisier"] = os.path.basename(zip_filepath)
                src_filepaths.append(zip_filepath)
            else:
                src_filepaths.append(item["fisier"])
                item["fisier"] = os.path.basename(item["fisier"])

        ri_files_path = get_extracts_path("ri")
        ri_files = []
        for sfp in src_filepaths:
            fp = shutil.copy2(sfp, os.path.join(ri_files_path, os.path.basename(sfp))) 
            ri_files.append(fp)

        df = pd.DataFrame(data)
        df = df.drop(columns=["mijloc_fix", "db_id"])
        df = df.rename(
            columns={
                "nr_crt": "Nr.Crt.",
                "nume_cheltuiala": "Denumirea elementelor inventariate",
                "deducere_in_ron": "Valoare inventar",
                "data_inserarii": "Data",
                "fisier": "Document",
            }
        )

        extracts_path = get_extracts_path()

        if filetype == "xlsx":
            ri_fp = os.path.join(extracts_path, "registru_inventar.xlsx")
            df.to_excel(ri_fp, index=False)
            make_excel_pretty(ri_fp)
        elif filetype == "csv":
            ri_fp = os.path.join(extracts_path, "registru_inventar.csv")
            df.to_csv(ri_fp, index=False)
        else:
            return redirect("/registre/")
        
        zip_filename = os.path.join(extracts_path, "registru_inventar.zip")
        with ZipFile(zip_filename, "w") as zipf:
            for file in ri_files:
                zipf.write(file, os.path.join("documente", os.path.basename(file)))
            zipf.write(ri_fp, os.path.basename(ri_fp))
            
        response = HttpResponse(
            open(zip_filename, "rb"), content_type="application/zip"
        )
        response["Content-Disposition"] = (
            f"attachment; filename={os.path.basename(zip_filename)}"
        )
        return response



class RegistreView(View):

    def get(self, request):
        overview_data = get_cards_and_charts_data(request)
        registru_fiscal = get_registru_de_evidenta_fiscala(
            request,
            overview_data["total_incasari_brut"],
            overview_data["total_incasari_net"],
            overview_data["total_cheltuieli"],
        )
        registru_jurnal_incasari_si_plati = get_registru_jurnal_incasari_si_plati(
            request
        )
        registru_inventar = get_registru_inventar()

        versiune_noua_disponibila = new_version_available()

        return render(
            request,
            "registre.html",
            context={
                **overview_data,
                "versiune_noua_disponibila": versiune_noua_disponibila, 
                "rjip": registru_jurnal_incasari_si_plati,
                "ref": registru_fiscal,
                "ri": registru_inventar,
            },
        )


def get_obiecte_inventar():
    results = CheltuialaModel.objects.filter(
        (Q(obiect_de_inventar=True) | Q(mijloc_fix=True)) & Q(scos_din_uz=False)
    ).order_by("data_inserarii")

    return results


def get_registru_inventar(dbid: bool = True, obiecte_inventar = None):

    if obiecte_inventar is None:
        obiecte_inventar = get_obiecte_inventar()

    idx = 1
    rows = []
    for item in obiecte_inventar:

        data = {
            "nr_crt": idx,
            "nume_cheltuiala": item.nume_cheltuiala,
            "deducere_in_ron": item.deducere_in_ron,
            "data_inserarii": item.data_inserarii.isoformat(),
            "fisier": item.fisier.path,
            "mijloc_fix": item.mijloc_fix,
        }

        if dbid:
            data.update({"db_id": item.id})

        rows.append(data)
        idx += 1

    return rows


def get_incasari_pe_surse(anul: int):

    incasari_activitate_principala = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.ACTIVITATE_PRINCIPALA, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_activitate_principala = incasari_activitate_principala["total"] or 0

    incasari_alte_surse = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.ALTE_SURSE, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_alte_surse = incasari_alte_surse["total"] or 0

    incasari_inchirieri = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.INCHIRIERI, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_inchirieri = incasari_inchirieri["total"] or 0

    incasari_castig_investitii = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.CASTIG_INVESTITII, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_castig_investitii = incasari_castig_investitii["total"]

    incasari_prop_intelectuala = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.DREPTURI_PROP_INTELECTUALA, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_prop_intelectuala = incasari_prop_intelectuala["total"]

    incasari_agricultura = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.AGRICULTURA, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_agricultura = incasari_agricultura["total"]

    incasari_dividente = IncasariModel.objects.filter(
        sursa_venit=SursaVenit.DIVIDENTE_VENIT_DISTRUBUIT, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    incasari_dividente = incasari_dividente["total"]

    incasari_pe_surse_de_venit = []

    if incasari_activitate_principala:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.ACTIVITATE_PRINCIPALA.value,
                "valoare": incasari_activitate_principala,
            }
        )

    if incasari_alte_surse:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.ALTE_SURSE.value,
                "valoare": incasari_alte_surse,
            }
        )

    if incasari_inchirieri:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.INCHIRIERI.value,
                "valoare": incasari_inchirieri,
            }
        )

    if incasari_castig_investitii:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.CASTIG_INVESTITII.value,
                "valoare": incasari_castig_investitii,
            }
        )

    if incasari_prop_intelectuala:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.DREPTURI_PROP_INTELECTUALA.value,
                "valoare": incasari_prop_intelectuala,
            }
        )

    if incasari_agricultura:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.AGRICULTURA.value,
                "valoare": incasari_agricultura,
            }
        )

    if incasari_dividente:
        incasari_pe_surse_de_venit.append(
            {
                "nume": SursaVenit.DIVIDENTE_VENIT_DISTRUBUIT.value,
                "valoare": incasari_dividente,
            }
        )

    return incasari_pe_surse_de_venit


def get_cheltuieli_pe_deductibilitate(anul: int):

    cheltuieli_pe_deductibilitate = []

    cheltuieli_d_integral = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL, data_inserarii__year=anul
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_integral = cheltuieli_d_integral["total"]

    if cheltuieli_d_integral:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_INTEGRAL.value,
                "valoare": cheltuieli_d_integral,
            }
        )

    cheltuieli_d_integral_inventar = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_integral_inventar = cheltuieli_d_integral_inventar["total"]

    if cheltuieli_d_integral_inventar:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR.value,
                "valoare": cheltuieli_d_integral_inventar,
            }
        )

    cheltuieli_d_integral_salarii = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_integral_salarii = cheltuieli_d_integral_salarii["total"]

    if cheltuieli_d_integral_salarii:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII.value,
                "valoare": cheltuieli_d_integral_salarii,
            }
        )

    cheltuieli_d_integral_amortizari = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_integral_amortizari = cheltuieli_d_integral_amortizari["total"]

    if cheltuieli_d_integral_amortizari:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.value,
                "valoare": cheltuieli_d_integral_amortizari,
            }
        )

    cheltuieli_d_partial_auto_casa_utilizati = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_auto_casa_utilizati = cheltuieli_d_partial_auto_casa_utilizati[
        "total"
    ]

    if cheltuieli_d_partial_auto_casa_utilizati:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI.value,
                "valoare": cheltuieli_d_partial_auto_casa_utilizati,
            }
        )

    cheltuieli_d_partial_sport_2024 = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_sport_2024 = cheltuieli_d_partial_sport_2024["total"]

    if cheltuieli_d_partial_sport_2024:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024.value,
                "valoare": cheltuieli_d_partial_sport_2024,
            }
        )

    cheltuieli_d_partial_pensie_p3 = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_pensie_p3 = cheltuieli_d_partial_pensie_p3["total"]

    if cheltuieli_d_partial_pensie_p3:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3.value,
                "valoare": cheltuieli_d_partial_pensie_p3,
            }
        )

    cheltuieli_d_partial_asig_medicale = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_asig_medicale = cheltuieli_d_partial_asig_medicale["total"]

    if cheltuieli_d_partial_asig_medicale:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT.value,
                "valoare": cheltuieli_d_partial_asig_medicale,
            }
        )

    cheltuieli_d_partial_protocol = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_protocol = cheltuieli_d_partial_protocol["total"]

    if cheltuieli_d_partial_protocol:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value,
                "valoare": cheltuieli_d_partial_protocol,
            }
        )

    cheltuieli_d_partial_sociale = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_sociale = cheltuieli_d_partial_sociale["total"]

    if cheltuieli_d_partial_sociale:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE.value,
                "valoare": cheltuieli_d_partial_sociale,
            }
        )

    cheltuieli_d_partial_contrib_obligatorii = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_contrib_obligatorii = cheltuieli_d_partial_contrib_obligatorii[
        "total"
    ]

    if cheltuieli_d_partial_contrib_obligatorii:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG.value,
                "valoare": cheltuieli_d_partial_contrib_obligatorii,
            }
        )

    cheltuieli_d_partial_cotizatii_voluntare = CheltuialaModel.objects.filter(
        deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG,
        data_inserarii__year=anul,
    ).aggregate(total=Sum("suma_in_ron"))
    cheltuieli_d_partial_cotizatii_voluntare = cheltuieli_d_partial_cotizatii_voluntare[
        "total"
    ]

    if cheltuieli_d_partial_cotizatii_voluntare:
        cheltuieli_pe_deductibilitate.append(
            {
                "nume": Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG.value,
                "valoare": cheltuieli_d_partial_cotizatii_voluntare,
            }
        )

    return cheltuieli_pe_deductibilitate


def get_registru_de_evidenta_fiscala(
    request, total_incasari_brut, total_incasari_net, total_cheltuieli
):
    anul = request.GET.get("anul")
    anul = int(anul) if anul else timezone.now().year

    incasari_pe_surse_de_venit = get_incasari_pe_surse(anul)
    cheltuieli_pe_deductibilitate = get_cheltuieli_pe_deductibilitate(anul)

    rows = [
        {
            "nr_crt": 1,
            "elemente_de_calcul": "Total incasari brut:",
            "valoare": total_incasari_brut,
            "anul": anul,
        }
    ]

    idx = None

    if len(incasari_pe_surse_de_venit) > 0:
        for idx, item in enumerate(incasari_pe_surse_de_venit, start=2):
            rows.append(
                {
                    "nr_crt": idx,
                    "elemente_de_calcul": item["nume"],
                    "valoare": item["valoare"],
                    "anul": anul,
                }
            )
        idx += 1

    idx = idx or 2
    rows.append(
        {
            "nr_crt": idx,
            "elemente_de_calcul": "Total cheltuieli:",
            "valoare": total_cheltuieli,
            "anul": anul,
        }
    )

    if len(cheltuieli_pe_deductibilitate) > 0:
        idx += 1
        for idx, item in enumerate(cheltuieli_pe_deductibilitate, start=idx):
            rows.append(
                {
                    "nr_crt": idx,
                    "elemente_de_calcul": item["nume"],
                    "valoare": item["valoare"],
                    "anul": anul,
                }
            )

    idx += 1
    rows.append(
        {
            "nr_crt": idx,
            "elemente_de_calcul": "Venit net realizat:",
            "valoare": total_incasari_net,
            "anul": anul,
        }
    )

    return rows


LUNI_RO = {
    1: "Ianuarie",
    2: "Februarie",
    3: "Martie",
    4: "Aprilie",
    5: "Mai",
    6: "Iunie",
    7: "Iulie",
    8: "August",
    9: "Septembrie",
    10: "Octombrie",
    11: "Noiembrie",
    12: "Decembrie",
}


def get_year_from_request(request):
    anul = request.GET.get("anul")
    anul = int(anul) if anul else timezone.now().year
    return anul

def incasari_cheltuieli_dupa_anul_inserarii(anul: int):
    incasari = IncasariModel.objects.filter(data_inserarii__year=anul)
    cheltuieli = CheltuialaModel.objects.filter(data_inserarii__year=anul)
    return incasari, cheltuieli


def get_registru_jurnal_incasari_si_plati(request, incasari = None, cheltuieli = None):
    anul = get_year_from_request(request)

    if incasari == None and cheltuieli == None:
        incasari, cheltuieli = incasari_cheltuieli_dupa_anul_inserarii(anul)

    combined_data = sorted(
        itertools.chain(incasari, cheltuieli), key=lambda x: x.data_inserarii
    )

    result = []
    total_incasari_numerar = 0
    total_incasari_bancar = 0
    total_cheltuieli_numerar = 0
    total_cheltuieli_bancar = 0
    current_month = None
    prev_month = None
    for idx, entry in enumerate(combined_data, start=1):

        if current_month is None:
            prev_month = entry.data_inserarii.month

        current_month = entry.data_inserarii.month

        if isinstance(entry, IncasariModel):

            incasari_numerar = (
                entry.suma_in_ron if entry.tip_tranzactie == "NUMERAR" else 0
            )
            incasari_bancar = (
                entry.suma_in_ron if entry.tip_tranzactie == "BANCAR" else 0
            )

            total_incasari_numerar += incasari_numerar
            total_incasari_bancar += incasari_bancar

            result.append(
                {
                    "nr_crt": idx,
                    "data": entry.data_inserarii.isoformat(),
                    "documentul": entry.fisier,
                    "documentId": str(entry.fisier).split("_")[0],
                    "felul_operatiunii": "Incasare",
                    "incasari_numerar": incasari_numerar,
                    "incasari_banca": incasari_bancar,
                    "plati_numerar": 0,
                    "plati_banca": 0,
                    "end_of_month": False,
                }
            )

        else:

            cheltuieli_numerar = (
                entry.suma_in_ron if entry.tip_tranzactie == "NUMERAR" else 0
            )
            cheltuieli_bancar = (
                entry.suma_in_ron if entry.tip_tranzactie == "BANCAR" else 0
            )

            total_cheltuieli_numerar += cheltuieli_numerar
            total_cheltuieli_bancar += cheltuieli_bancar

            result.append(
                {
                    "nr_crt": idx,
                    "data": entry.data_inserarii.isoformat(),
                    "documentul": entry.fisier,
                    "documentId": str(entry.fisier).split("_")[0],
                    "felul_operatiunii": f"Cheltuiala {entry.nume_cheltuiala}",
                    "incasari_numerar": 0,
                    "incasari_banca": 0,
                    "plati_numerar": cheltuieli_numerar,
                    "plati_banca": cheltuieli_bancar,
                    "end_of_month": False,
                }
            )

        if current_month > prev_month:
            prev_month = current_month

            result.append(
                {
                    "nr_crt": "-",
                    "data": "-",
                    "documentul": "-",
                    "documentId": None,
                    "felul_operatiunii": f"Calcul total luna {LUNI_RO[current_month]}",
                    "incasari_numerar": round(total_incasari_numerar, 2),
                    "incasari_banca": round(total_incasari_bancar, 2),
                    "plati_numerar": round(total_cheltuieli_numerar, 2),
                    "plati_banca": round(total_cheltuieli_bancar, 2),
                    "end_of_month": True,
                }
            )

            total_incasari_numerar = 0
            total_incasari_bancar = 0
            total_cheltuieli_numerar = 0
            total_cheltuieli_bancar = 0

    return result


def get_cards_and_charts_data(request):

    current_year = timezone.now().year
    anul = request.GET.get("anul")
    valuta = request.GET.get("valuta") or "RON"
    in_euro = valuta == "EUR"
    anul = int(anul) if anul else current_year

    # CALCUL INCASARI, CHELTUIELI
    try:
        total_neincasate = IncasariModel.get_total_neincasate(anul)
        total_incasari_brut = IncasariModel.get_total_incasari(anul)
        try:
            total_cheltuieli = CheltuialaModel.get_total_cheltuieli(anul)
        except Exception as err:
            print("0 total cheltuieli", err)
            total_cheltuieli = 0

        total_incasari_net = round((total_incasari_brut - total_cheltuieli), 2)

        if total_incasari_net <= 0:
            total_incasari_net = 0

        cheltuieli = CheltuialaModel.objects.all()
        if cheltuieli:
            c_newest_date = cheltuieli.latest("data_inserarii")
            c_oldest_date = cheltuieli.earliest("data_inserarii")

        incasari = IncasariModel.objects.all()
        if incasari:
            i_newest_date = incasari.latest("data_inserarii")
            i_oldest_date = incasari.earliest("data_inserarii")

        if cheltuieli and incasari:
            years_list = [
                c_newest_date.data_inserarii.year,
                i_newest_date.data_inserarii.year,
                c_oldest_date.data_inserarii.year,
                i_oldest_date.data_inserarii.year,
                current_year,
            ]
        elif cheltuieli:
            years_list = [
                c_newest_date.data_inserarii.year,
                c_oldest_date.data_inserarii.year,
                current_year,
            ]
        elif incasari:
            years_list = [
                i_newest_date.data_inserarii.year,
                i_oldest_date.data_inserarii.year,
                current_year,
            ]
        else:
            years_list = [current_year]

        ani_inregistrati = reversed(range(min(years_list), max(years_list) + 1))

        incasari_pe_luni = IncasariModel.get_total_incasari_pe_luni(anul)
        cheltuieli_pe_luni = CheltuialaModel.get_total_cheltuieli_pe_luni(anul)

        media_url_chart_incasari_cheltuieli = create_bar_plot(
            anul, incasari_pe_luni, cheltuieli_pe_luni, valuta
        )

    except Exception as err:
        print("all-zero", err)
        total_neincasate = 0
        total_incasari_brut = 0
        total_incasari_net = 0
        total_cheltuieli = 0
        ani_inregistrati = [anul]
        media_url_chart_incasari_cheltuieli = create_bar_plot(
            anul, [0] * 12, [0] * 12, valuta
        )

    # CALCUL TAXE IMPOZITE
    la_stat = calculeaza_taxe_si_impozite(total_incasari_net, anul)
    total_platite_la_stat_pe_toti_anii = DocumenteModel.total_plati_la_stat()

    years = copy(ani_inregistrati)
    total_incasari_net_pe_toti_anii = 0
    total_incasari_brut_pe_toti_anii = 0
    total_cheltuieli_pe_toti_anii = 0
    total_de_platit_la_stat_pe_toti_anii = 0
    for yr in years:
        tib = IncasariModel.get_total_incasari(yr)
        tc = CheltuialaModel.get_total_cheltuieli(yr)
        total_cheltuieli_pe_toti_anii += tc
        total_incasari_brut_pe_toti_anii += tib
        incasari_net = round((tib - tc), 2)
        tiy = calculeaza_taxe_si_impozite(incasari_net, yr)["total_taxe_impozite"]
        total_de_platit_la_stat_pe_toti_anii += tiy

    total_incasari_net_pe_toti_anii = (
        total_incasari_brut_pe_toti_anii
        - total_cheltuieli_pe_toti_anii
        - total_de_platit_la_stat_pe_toti_anii
    )

    if total_incasari_net_pe_toti_anii <= 0:
        total_incasari_net_pe_toti_anii = 0

    total_incasari_net_pe_toti_anii = round(total_incasari_net_pe_toti_anii, 2)

    rest_de_plata_catre_stat = round(
        abs(total_platite_la_stat_pe_toti_anii - total_de_platit_la_stat_pe_toti_anii),
        2,
    )

    return {
        "anul": anul,
        "valuta": valuta,
        "ani_inregistrati": ani_inregistrati,
        "media_url_chart_incasari_cheltuieli": media_url_chart_incasari_cheltuieli,
        "rest_de_plata_catre_stat": (
            ron_to_eur(rest_de_plata_catre_stat, anul)
            if in_euro
            else rest_de_plata_catre_stat
        ),
        "total_platite_la_stat_pe_toti_anii": (
            ron_to_eur(total_platite_la_stat_pe_toti_anii, anul)
            if in_euro
            else total_platite_la_stat_pe_toti_anii
        ),
        "total_incasari_net_pe_toti_anii": (
            ron_to_eur(total_incasari_net_pe_toti_anii, anul)
            if in_euro
            else total_incasari_net_pe_toti_anii
        ),
        "total_neincasate": (
            ron_to_eur(total_neincasate, anul) if in_euro else total_neincasate
        ),
        "total_incasari_brut": (
            ron_to_eur(total_incasari_brut, anul) if in_euro else total_incasari_brut
        ),
        "total_incasari_net": (
            ron_to_eur(total_incasari_net, anul) if in_euro else total_incasari_net
        ),
        "total_cheltuieli": (
            ron_to_eur(total_cheltuieli, anul) if in_euro else total_cheltuieli
        ),
        "total_taxe_impozite": (
            ron_to_eur(la_stat["total_taxe_impozite"], anul)
            if in_euro
            else la_stat["total_taxe_impozite"]
        ),
        "cas_pensie": (
            ron_to_eur(la_stat["cas_pensie"], anul)
            if in_euro
            else la_stat["cas_pensie"]
        ),
        "cass_sanatate": (
            ron_to_eur(la_stat["cass_sanatate"], anul)
            if in_euro
            else la_stat["cass_sanatate"]
        ),
        "impozit_pe_venit": (
            ron_to_eur(la_stat["impozit_pe_venit"], anul)
            if in_euro
            else la_stat["impozit_pe_venit"]
        ),
    }


def create_bar_plot(
    anul: int,
    incasari_pe_luni: list[float],
    cheltuieli_pe_luni: list[float],
    currency: str = "RON",
):

    if currency == "EUR":
        incasari_pe_luni = [ron_to_eur(i, anul) for i in incasari_pe_luni]
        cheltuieli_pe_luni = [ron_to_eur(c, anul) for c in cheltuieli_pe_luni]

    index_col = f"Anul {anul}"

    data = {
        index_col: [
            "Ianuarie",
            "Februarie",
            "Martie",
            "Aprilie",
            "Mai",
            "Iunie",
            "Iulie",
            "August",
            "Septembrie",
            "Octombrie",
            "Noiembrie",
            "Decembrie",
        ],
        "Incasari": incasari_pe_luni,
        "Cheltuieli": cheltuieli_pe_luni,
    }

    # Create DataFrame
    df = pd.DataFrame(data)

    # Set the 'index_col' column as the index
    df.set_index(index_col, inplace=True)

    # Define colors
    dark = "#181c25"
    green = "#33790F"
    amber = "#D8A100"

    # Plot grouped bar chart with custom colors
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(len(df) * 1.5, 6))
    # Set 'Incasari' to green and 'Cheltuieli' to amber
    df.plot(kind="bar", width=0.8, ax=ax, color=[green, amber])

    # Add numbers on the bars, flipped vertically
    for container in ax.containers:
        ax.bar_label(
            container, label_type="edge", rotation=None, color="white", fontsize=10
        )

    # Set labels and title
    ax.set_xlabel(index_col, color="white")
    ax.set_ylabel(f"Suma {currency}", color="white")
    ax.set_title(f"Incasari vs Cheltuieli ({currency})", color="white")

    # Change x-axis label color to white
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    # Change background color to dark
    ax.set_facecolor(dark)
    fig.patch.set_facecolor(dark)

    # Adjust layout to add padding
    plt.tight_layout(pad=3.0)

    # Save the plot as an SVG file
    svgname = f"incasari_vs_cheltuieli_bar_chart_{currency}.svg"
    svgfp = os.path.join(MEDIA_ROOT, svgname)
    plt.savefig(svgfp, format="svg")
    plt.close(fig)

    return "/media/" + svgname
