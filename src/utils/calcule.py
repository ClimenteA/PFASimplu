from core.settings import get_salarii_minim_brut_local

from .decimale import D, rotund2, rotund4


def get_venit_net(year: int):
    """venit net aka baza de calcul"""
    from cheltuieli.models import CheltuialaModel
    from incasari.models import IncasariModel

    total_incasari = IncasariModel.get_total_incasari(year)
    total_cheltuieli = CheltuialaModel.get_total_cheltuieli(year)

    return D(total_incasari) - D(total_cheltuieli)


def get_venit_brut(year: int):
    from incasari.models import IncasariModel

    total_incasari = IncasariModel.get_total_incasari(year)
    return D(total_incasari)


def calculeaza_taxe_si_impozite(
    venit_net,
    anul: int,
    scutit_cas: bool = False,
    scutit_cass: bool = False,
    scutit_impozit: bool = False,
):
    """Calculul taxelor, cu Decimal (4 zecimale in calcul, 2 la sumele finale)."""
    venit_net = D(venit_net)
    minim_brute_an_val = get_salarii_minim_brut_local()

    if anul in minim_brute_an_val:
        salariuMinimBrut = D(minim_brute_an_val[anul])
    else:
        salariuMinimBrut = D(minim_brute_an_val[max(list(minim_brute_an_val.keys()))])

    CAS = D(0)
    CASS = D(0)
    impozitPeVenit = D(0)
    total = D(0)

    ProcentCAS = D(25)  # Pensie
    ProcentCASS = D(10)  # Sanatate
    ProcentImpozitVenit = D(10)  # Impozit pe venit

    plafon6 = salariuMinimBrut * 6
    plafon12 = salariuMinimBrut * 12
    plafon24 = salariuMinimBrut * 24
    plafon60 = salariuMinimBrut * 60
    plafon72 = salariuMinimBrut * 72

    if anul <= 2022:
        if venit_net > plafon12:
            CAS = rotund4(ProcentCAS * plafon12 / D(100))
            CASS = rotund4(ProcentCASS * plafon12 / D(100))
        impozitPeVenit = rotund4(ProcentImpozitVenit * (venit_net - CAS) / D(100))

    elif anul == 2023:
        if venit_net > plafon6:
            CASS = rotund4(ProcentCASS * plafon6 / D(100))

        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = rotund4(ProcentCAS * plafon12 / D(100))
            CASS = rotund4(ProcentCASS * plafon12 / D(100))

        if venit_net > plafon24:
            CAS = rotund4(ProcentCAS * plafon24 / D(100))
            CASS = rotund4(ProcentCASS * plafon24 / D(100))

        impozitPeVenit = rotund4(ProcentImpozitVenit * (venit_net - CAS) / D(100))

    elif anul >= 2024:
        # CAS (art. 148): baza aleasa, minim 12 salarii intre 12 si 24 salarii,
        # minim 24 salarii de la 24 salarii in sus; sub 12 salarii nu se datoreaza.
        if venit_net > plafon12 and venit_net <= plafon24:
            CAS = rotund4(ProcentCAS * plafon12 / D(100))
        if venit_net > plafon24:
            CAS = rotund4(ProcentCAS * plafon24 / D(100))

        # CASS (art. 170 alin. 1, art. 156): 10% din venitul net, cu baza minima de
        # 6 salarii si baza maxima de 60 salarii (2024, 2025) sau 72 salarii (din 2026,
        # Legea 239/2025). Treptele 6/12/24 se aplica doar altor categorii de venituri
        # (art. 170 alin. 3), nu activitatilor independente.
        plafon_maxim_cass = plafon72 if anul >= 2026 else plafon60
        if anul >= 2025 and venit_net <= 0:
            baza_cass = D(0)
        else:
            baza_cass = min(max(venit_net, plafon6), plafon_maxim_cass)
        CASS = rotund4(ProcentCASS * baza_cass / D(100))

        impozitPeVenit = rotund4(
            ProcentImpozitVenit * (venit_net - CAS - CASS) / D(100)
        )

    if scutit_cas:
        CAS = D(0)

    if scutit_cass:
        CASS = D(0)

    if scutit_impozit:
        impozitPeVenit = D(0)

    total = CAS + CASS + impozitPeVenit

    return {
        # Sumele finale se rotunjesc cu .5 in sus, la 2 zecimale.
        "cas_pensie": rotund2(CAS),
        "cass_sanatate": rotund2(CASS),
        "impozit_pe_venit": rotund2(impozitPeVenit),
        "total_taxe_impozite": rotund2(total),
    }
