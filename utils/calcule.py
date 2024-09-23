import requests
import textwrap
from datetime import timedelta
from django.utils import timezone
from setari.models import VersiuneModel


def get_venit_net(year: int):
    """venit net aka baza de calcul"""
    from incasari.models import IncasariModel
    from cheltuieli.models import CheltuialaModel

    total_incasari = IncasariModel.get_total_incasari(year)
    total_cheltuieli = CheltuialaModel.get_total_cheltuieli(year)

    return total_incasari - total_cheltuieli


def get_venit_brut(year: int):
    from incasari.models import IncasariModel

    total_incasari = IncasariModel.get_total_incasari(year)
    return total_incasari


def calcul_taxe_impozite_local(venit_net: float, anul: int):
    """
    versiune = "2.0.0"
    """

    minim_brute_an_val = {
        2020: 2230,
        2021: 2300,
        2022: 2550,
        2023: 3000,
        2024: 3300,
        2025: 3700,
    }

    if anul in minim_brute_an_val:
        salariuMinimBrut = minim_brute_an_val[anul]
    else:
        salariuMinimBrut = minim_brute_an_val[max(list(minim_brute_an_val.keys()))]

    CAS = 0.0
    CASS = 0.0
    impozitPeVenit = 0.0
    total = 0.0

    ProcentCAS = 25  # Pensie
    ProcentCASS = 10  # Sanatate
    ProcentImpozitVenit = 10  # Impozit pe venit

    plafon6 = salariuMinimBrut * 6
    plafon12 = salariuMinimBrut * 12
    plafon24 = salariuMinimBrut * 24
    plafon60 = salariuMinimBrut * 60

    if anul <= 2022:
        if venit_net > plafon12:
            CAS = ProcentCAS * plafon12 / 100
            CASS = ProcentCASS * plafon12 / 100
        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS) / 100

    if anul == 2023:

        if venit_net > plafon6:
            CASS = ProcentCASS * plafon6 / 100

        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = ProcentCAS * plafon12 / 100
            CASS = ProcentCASS * plafon12 / 100

        if venit_net > plafon24:
            CAS = ProcentCAS * plafon24 / 100
            CASS = ProcentCASS * plafon24 / 100

        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS) / 100

    if anul >= 2024:

        if venit_net <= plafon6:
            CASS = ProcentCASS * plafon6 / 100

        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = ProcentCAS * plafon12 / 100
            CASS = ProcentCASS * plafon12 / 100

        if venit_net > plafon24:
            CAS = ProcentCAS * plafon24 / 100
            CASS = ProcentCASS * plafon24 / 100

        if venit_net > plafon60:
            CASS = ProcentCASS * plafon60 / 100

        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS - CASS) / 100

    if venit_net <= 0:
        impozitPeVenit = 0

    total = CAS + CASS + impozitPeVenit

    return {
        "cas_pensie": round(CAS, 2),
        "cass_sanatate": round(CASS, 2),
        "impozit_pe_venit": round(impozitPeVenit, 2),
        "total_taxe_impozite": round(total, 2),
    }


def ultimul_calcul_taxe_impozite():

    one_day_ago = timezone.now() - timedelta(days=1)

    items = VersiuneModel.objects.filter(
        ultima_actualizare__gte=one_day_ago,
        cod_calcul_taxe_impozite__isnull=False,
    )

    if len(items) > 0:
        return items[0].cod_calcul_taxe_impozite

    response = requests.get(
        "https://gist.githubusercontent.com/ClimenteA/a11ce736af219c594adf0926b978e26f/raw"
    )
    formatted_code = textwrap.dedent(response.text)

    instance = VersiuneModel.objects.first()
    if instance:
        instance.ultima_actualizare = timezone.now()
        instance.cod_calcul_taxe_impozite = formatted_code
        instance.save()
    else:
        VersiuneModel.objects.create(
            ultima_actualizare=timezone.now(),
            cod_calcul_taxe_impozite=formatted_code,
        )

    print("Ultima versiune de calcul taxe si impozite a fost preluata.")
    return formatted_code


def calculeaza_taxe_si_impozite(venit_net: float, anul: int):
    # try:
    #     formatted_code = ultimul_calcul_taxe_impozite()
    #     exec(formatted_code, globals())
    #     if "calcul_taxe_impozite" in globals():
    #         return calcul_taxe_impozite(venit_net, anul)  # type: ignore
    #     else:
    #         raise NameError("Functia 'calcul_taxe_impozite' nu a putut fi gasita.")
    # except Exception as err:
    #     print(err)
    #     print("calcul din local")
    return calcul_taxe_impozite_local(venit_net, anul)
