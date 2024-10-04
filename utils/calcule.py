from .github_data import get_salarii_minim_brut

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


def calculeaza_taxe_si_impozite(venit_net: float, anul: int):

    minim_brute_an_val = get_salarii_minim_brut()

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

    if venit_net <= plafon6:
        impozitPeVenit = 0

    total = CAS + CASS + impozitPeVenit

    return {
        "cas_pensie": round(CAS, 2),
        "cass_sanatate": round(CASS, 2),
        "impozit_pe_venit": round(impozitPeVenit, 2),
        "total_taxe_impozite": round(total, 2),
    }
