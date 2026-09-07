from .github_data import get_salarii_minim_brut


def get_venit_net(year: int):
    """venit net aka baza de calcul"""
    from cheltuieli.models import CheltuialaModel
    from incasari.models import IncasariModel

    total_incasari = IncasariModel.get_total_incasari(year)
    total_cheltuieli = CheltuialaModel.get_total_cheltuieli(year)

    return total_incasari - total_cheltuieli


def get_venit_brut(year: int):
    from incasari.models import IncasariModel

    total_incasari = IncasariModel.get_total_incasari(year)
    return total_incasari


def calculeaza_taxe_si_impozite(
    venit_net: float,
    anul: int,
    scutit_cas: bool = False,
    scutit_cass: bool = False,
    scutit_impozit: bool = False,
):

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
    plafon72 = salariuMinimBrut * 72

    if anul <= 2022:
        if venit_net > plafon12:
            CAS = ProcentCAS * plafon12 / 100
            CASS = ProcentCASS * plafon12 / 100
        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS) / 100

    elif anul == 2023:

        if venit_net > plafon6:
            CASS = ProcentCASS * plafon6 / 100

        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = ProcentCAS * plafon12 / 100
            CASS = ProcentCASS * plafon12 / 100

        if venit_net > plafon24:
            CAS = ProcentCAS * plafon24 / 100
            CASS = ProcentCASS * plafon24 / 100

        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS) / 100

    elif anul >= 2024:
        # CAS (art. 148): baza aleasa, minim 12 salarii intre 12 si 24 salarii,
        # minim 24 salarii de la 24 salarii in sus; sub 12 salarii nu se datoreaza.
        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = ProcentCAS * plafon12 / 100
        if venit_net > plafon24:
            CAS = ProcentCAS * plafon24 / 100

        # CASS (art. 170 alin. 1, art. 156): 10% din venitul net, cu baza minima de
        # 6 salarii si baza maxima de 60 salarii (2024, 2025) sau 72 salarii (din 2026,
        # Legea 239/2025). Treptele 6/12/24 se aplica doar altor categorii de venituri
        # (art. 170 alin. 3), nu activitatilor independente.
        plafon_maxim_cass = plafon72 if anul >= 2026 else plafon60
        if anul >= 2025 and venit_net <= 0:
            baza_cass = 0
        else:
            baza_cass = min(max(venit_net, plafon6), plafon_maxim_cass)
        CASS = ProcentCASS * baza_cass / 100

        impozitPeVenit = ProcentImpozitVenit * (venit_net - CAS - CASS) / 100

    if scutit_cas:
        CAS = 0
    
    if scutit_cass:
        CASS = 0
    
    if scutit_impozit:
        impozitPeVenit = 0

    total = CAS + CASS + impozitPeVenit

    return {
        "cas_pensie": round(CAS, 2),
        "cass_sanatate": round(CASS, 2),
        "impozit_pe_venit": round(impozitPeVenit, 2),
        "total_taxe_impozite": round(total, 2),
    }
