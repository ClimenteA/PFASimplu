from .decimale import D, rotund2
from .parametri import get_parametri


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


def calculeaza_cass_trepte(venit_cumulat, anul: int):
    """CASS pentru veniturile de la art. 155 alin. (1) lit. c)-h).

    Spre deosebire de activitatile independente (baza liniara), aici baza se
    stabileste pe trepte: 6 / 12 / 24 de salarii minime, conform art. 170
    alin. (2)-(3) din Codul fiscal. Sub prima treapta nu se datoreaza CASS.
    """
    venit_cumulat = D(venit_cumulat)
    parametri = get_parametri(anul)
    salariu = D(parametri["salariu_minim_brut"])
    cota = D(str(parametri["cote"]["cass"]))
    trepte = sorted(
        D(treapta) for treapta in parametri["cass_salarii"]["trepte_alte_categorii"]
    )

    if not trepte or venit_cumulat < salariu * trepte[0]:
        return D(0)

    raport = venit_cumulat / salariu
    baza_salarii = trepte[0]
    for treapta in trepte:
        if raport >= treapta:
            baza_salarii = treapta
    return D(cota * salariu * baza_salarii)


def calculeaza_taxe_si_impozite(
    venit_net,
    anul: int,
    scutit_cas: bool = False,
    scutit_cass: bool = False,
    scutit_impozit: bool = False,
    alte_venituri=None,
):
    """Calculul taxelor, cu Decimal (toate zecimalele in calcul, 2 la finale).

    Cotele, salariul minim si plafoanele vin din fisierul de parametri fiscali
    pe ani (utils/parametri.py), cu fallback pe ultimul an disponibil.

    ``venit_net`` e venitul net total al anului; ``alte_venituri`` reprezinta
    partea din el care provine din categorii diferite de activitatea
    independenta (art. 155 alin. 1 lit. c)-h) si se impune pe trepte.
    """
    venit_net = D(venit_net)
    alte_venituri = D(alte_venituri or 0)
    venit_activitate = max(venit_net - alte_venituri, D(0))
    parametri = get_parametri(anul)
    salariuMinimBrut = D(parametri["salariu_minim_brut"])

    ProcentCAS = D(str(parametri["cote"]["cas"])) * D(100)
    ProcentCASS = D(str(parametri["cote"]["cass"])) * D(100)
    ProcentImpozitVenit = D(str(parametri["cote"]["impozit_pe_venit"])) * D(100)

    plafon12 = salariuMinimBrut * D(parametri["cas_salarii"]["min"])
    plafon24 = salariuMinimBrut * D(parametri["cas_salarii"]["max"])
    plafon6 = salariuMinimBrut * D(parametri["cass_salarii"]["min"])
    plafon_maxim_cass = salariuMinimBrut * D(parametri["cass_salarii"]["max"])

    CAS = D(0)
    CASS = D(0)
    impozitPeVenit = D(0)

    # CAS (art. 148): sub 12 salarii nu se datoreaza; intre 12 si 24 baza e
    # minim 12 salarii; de la 24 de salarii in sus baza e 24 de salarii.
    if plafon12 < venit_net <= plafon24:
        CAS = D(ProcentCAS * plafon12 / D(100))
    elif venit_net > plafon24:
        CAS = D(ProcentCAS * plafon24 / D(100))

    # CASS pentru activitatea independenta: baza liniara, cu minim 6 salarii
    # si maximul anului; pierdere sau venit zero -> zero (art. 174 alin. 2).
    if venit_activitate <= 0:
        cass_activitate = D(0)
    else:
        baza_cass = min(max(venit_activitate, plafon6), plafon_maxim_cass)
        cass_activitate = D(ProcentCASS * baza_cass / D(100))

    # CASS pentru celelalte categorii se calculeaza pe trepte (art. 170 alin. 3).
    # Cand exista ambele categorii se pastreaza o singura contributie, la
    # nivelul cel mai mare: regulile de diferenta sunt la art. 174 alin. (6)-(7)
    # si art. 174^1 alin. (9)-(11) din Codul fiscal.
    CASS = max(cass_activitate, calculeaza_cass_trepte(alte_venituri, anul))

    # Impozitul se aplica venitului net anual impozabil, diminuat cu CAS si
    # CASS datorate (art. 118 alin. 2 lit. b), inclusiv in cazul altor surse.
    baza_impozit = max(venit_net - CAS - CASS, D(0))
    impozitPeVenit = D(ProcentImpozitVenit * baza_impozit / D(100))

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
