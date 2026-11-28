"""Toate calculele aplicate unei cheltuieli.

Sursa de adevar sunt doar campurile introduse de utilizator. Valorile care
apar in rapoarte (suma in RON, deducere, amortizare, TVA autolichidat) se
calculeaza aici, intr-un singur loc, si sunt expuse ca proprietati pe model.
"""

import datetime

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db.models import Count, Max, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.cursuri import curs_bnr_ziua_bancara_anterioara, to_ron
from utils.decimale import D, rotund2
from utils.parametri import get_parametri
from utils.tari import (
    TARI_NON_UE_CHOICES,
    TARI_UE_CHOICES,
    este_tara_ue,
)

from .catalog import CODURI_CLASIFICARE
from .models import (
    MIJLOC_FIX_CODURI,
    CheltuialaModel,
    Deductibilitate,
    TipAchizitie,
)

UE_CODES = [cod for cod, _ in TARI_UE_CHOICES]
NON_UE_CODES = [cod for cod, _ in TARI_NON_UE_CHOICES]


def q_ue():
    return Q(furnizor_tara__in=UE_CODES)


def q_non_ue():
    return Q(furnizor_tara__in=NON_UE_CODES)


def q_taxare_inversa():
    return Q(furnizor_tara__isnull=False) & ~Q(furnizor_tara="")


def q_mijloc_fix():
    return Q(deductibila__in=MIJLOC_FIX_CODURI)


def q_obiect_inventar():
    return Q(deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR)


def q_inventar():
    return q_mijloc_fix() | q_obiect_inventar()


def q_scos_din_uz():
    return Q(data_iesirii_din_uz__isnull=False)


# --- campuri derivate simple -------------------------------------------------


def tip_achizitie(c):
    if not c.furnizor_tara:
        return TipAchizitie.ROMANIA.value
    return (
        TipAchizitie.SERVICII_UE.value
        if este_tara_ue(c.furnizor_tara)
        else TipAchizitie.SERVICII_NON_UE.value
    )


def este_taxare_inversa(c):
    return bool(c.furnizor_tara)


def este_ue(c):
    return este_tara_ue(c.furnizor_tara)


def suma_in_ron(c):
    return to_ron(c.suma, c.valuta, c.data_inserarii)


def curs_bnr_aplicat(c):
    """Cursul zilei bancare anterioare inserarii, acelasi cu cel din suma_in_ron.

    Toate sumele unei facturi cu taxare inversa (suma, baza si TVA autolichidat)
    se convertesc cu acelasi curs, ca sa fie consistent intre registru, D301/D390
    si deducere.
    """
    if not este_taxare_inversa(c):
        return None
    return curs_bnr_ziua_bancara_anterioara(c.valuta, c.data_inserarii)


def baza_in_lei(c):
    if not este_taxare_inversa(c):
        return None
    return D(suma_in_ron(c))


def cota_tva_autolichidata(c):
    """Cota TVA standard pentru taxare inversa, din parametrii fiscali.

    Se aplica doar pentru furnizori straini; pentru cei romani nu exista
    taxare inversa.
    """
    if not c.furnizor_tara:
        return D(0)
    an = (
        c.data_facturii.year
        if c.data_facturii
        else (c.data_inserarii.year if c.data_inserarii else timezone.now().year)
    )
    return D(str(get_parametri(an)["cote"]["tva_standard"]))


def tva_autolichidata(c):
    if not este_taxare_inversa(c):
        return None
    return D(baza_in_lei(c)) * cota_tva_autolichidata(c)


# --- amortizare --------------------------------------------------------------


def clasificare(c):
    """Intoarce inregistrarea din catalog pentru un mijloc fix."""
    if c.deductibila not in MIJLOC_FIX_CODURI:
        return None
    if not c.data_punerii_in_functiune:
        raise ValidationError(
            _("Pentru un mijloc fix trebuie completata data punerii in functiune.")
        )
    cod = (c.cod_de_clasificare or "").strip()
    if cod and not cod.endswith("."):
        cod += "."
    potriviri = [x for x in CODURI_CLASIFICARE if x["cod_clasificare"] == cod]
    if not potriviri:
        raise ValidationError(
            _(
                "Codul de clasificare '{}' nu exista in catalogul mijloacelor fixe.".format(
                    c.cod_de_clasificare
                )
            )
        )
    return potriviri[0]


def grupa(c):
    item = clasificare(c)
    return item["grupa"] if item else None


def durata_normala_de_functionare(c):
    item = clasificare(c)
    return item["durata_amortizare_in_ani"] if item else None


def ani_amortizare(c):
    if c.deductibila not in MIJLOC_FIX_CODURI:
        return None
    if c.ani_amortizare:
        return int(c.ani_amortizare)
    return int(clasificare(c)["durata_amortizare_in_ani"].split("-")[0])


def data_inceperii_amortizarii(c):
    ani = ani_amortizare(c)
    if ani is None or not c.data_punerii_in_functiune:
        return None
    return (c.data_punerii_in_functiune + relativedelta(months=1)).replace(day=1)


def data_amortizarii_complete(c):
    ani = ani_amortizare(c)
    if ani is None or not c.data_punerii_in_functiune:
        return None
    return c.data_punerii_in_functiune + relativedelta(years=ani)


def amortizare_lunara(c):
    ani = ani_amortizare(c)
    if not ani:
        return None
    lunar = D(suma_in_ron(c)) / D(ani * 12)
    an = anul_darii_in_folosinta(c) or timezone.now().year
    parametri = get_parametri(an)
    procente = parametri["deductibilitati"]["procente"]

    # Sediu social folosit si in scop personal: amortizare deductibila 50%
    # (art. 28 alin. 12 lit. i^1 din Codul fiscal).
    if c.deductibila == Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA_SEDIU.value:
        lunar = D(lunar * D(str(procente["sediu_social"])))

    # Autoturisme M1: limita lunara de 1.500 lei (art. 28 alin. 14).
    # Optiunea cu exceptie (art. 28 alin. 14 lit. a)-d)) pastreaza amortizarea
    # integrala, deci nu se plafoneaza.
    if c.deductibila == Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA_M1.value:
        lunar = min(lunar, D(parametri["amortizare_auto_m1_lunar"]))

    return lunar


def cota_de_amortizare(c):
    lunar = amortizare_lunara(c)
    total = D(suma_in_ron(c))
    if lunar is None or not total:
        return None
    return rotund2(D(lunar) / total * D(100))


def anul_darii_in_folosinta(c):
    return c.data_punerii_in_functiune.year if c.data_punerii_in_functiune else None


def luna_darii_in_folosinta(c):
    return c.data_punerii_in_functiune.month if c.data_punerii_in_functiune else None


def anul_amortizarii_complete(c):
    data = data_amortizarii_complete(c)
    return data.year if data else None


def luna_amortizarii_complete(c):
    data = data_amortizarii_complete(c)
    return data.month if data else None


def obiect_de_inventar(c):
    return c.deductibila == Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR.value


def mijloc_fix(c):
    return c.deductibila in MIJLOC_FIX_CODURI


def scos_din_uz(c):
    return bool(c.data_iesirii_din_uz)


def luni_amortizare_active_in_an(c, an):
    inceput = data_inceperii_amortizarii(c)
    sfarsit = data_amortizarii_complete(c)
    if not inceput or not sfarsit:
        return []
    azi = timezone.now().date()
    luni = []
    for luna in range(1, 13):
        zi = datetime.date(an, luna, 1)
        if zi < inceput.replace(day=1) or zi > sfarsit:
            continue
        if scos_din_uz(c) and c.data_iesirii_din_uz and zi > c.data_iesirii_din_uz:
            continue
        if an == azi.year and luna > azi.month:
            continue
        luni.append(luna)
    return luni


def total_amortizari(an):
    total = D(0)
    for c in CheltuialaModel.objects.filter(q_mijloc_fix()):
        sfarsit = data_amortizarii_complete(c)
        inceput = data_inceperii_amortizarii(c)
        if not sfarsit or not inceput:
            continue
        if sfarsit.year < an or inceput.year > an:
            continue
        lunar = amortizare_lunara(c)
        if lunar:
            total += D(lunar) * D(len(luni_amortizare_active_in_an(c, an)))
    return total


# --- deductibilitate ---------------------------------------------------------

_EUR_CAP_CODURI = {
    Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024.value: "sport",
    Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3.value: "pensie_facultativa",
    Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_OCUPATIONALA.value: "pensie_ocupationala",
    Deductibilitate.DEDUCTIBILA_PARTIAL_PEPP.value: "pepp",
    Deductibilitate.DEDUCTIBILA_PARTIAL_ETF.value: "etf",
    Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT.value: "asig_med",
    Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG.value: "cotizatii",
}


def _eroare_plafon(remaining):
    remaining = rotund2(remaining)
    if remaining < 1:
        remaining = D(0)
    return ValidationError(
        _(
            "Nu putem deduce suma introdusa. Mai sunt {} RON disponibili pentru deducere.".format(
                remaining
            )
        )
    )


_CACHE = {}


def _reviziune(an):
    """Semnalatura datelor care pot schimba deducerile dintr-un an.

    Include si incasarile: plafonul de protocol (2%) depinde de venitul net,
    deci o incasare noua trebuie sa invalideze cache-ul deducerilor.
    """
    from incasari.models import IncasariModel

    cheltuieli = CheltuialaModel.objects.filter(data_inserarii__year=an).aggregate(
        n=Count("id"), m=Max("id"), u=Max("actualizat_la")
    )
    incasari = IncasariModel.objects.filter(data_incasarii__year=an).aggregate(
        n=Count("id"), u=Max("actualizat_la")
    )
    return (
        cheltuieli["n"],
        cheltuieli["m"],
        cheltuieli["u"],
        incasari["n"],
        incasari["u"],
    )


def calculeaza_deduceri_anului(an: int, candidat=None):
    """Dictionar {pk: deducere_in_ron} pentru tot anul.

     Regulile cu plafon anual se evalueaza in ordinea (data_inserarii, id), exact
     ca la introducerea randurilor in aplicatie. `candidat` inlocuieste randul
     cu acelasi pk (sau se adauga la final cand e nou) si permite validarea in
    ainte de salvare.
    """
    rev = _reviziune(an)
    if candidat is None and an in _CACHE and _CACHE[an][0] == rev:
        return _CACHE[an][1]

    rows = list(
        CheltuialaModel.objects.filter(data_inserarii__year=an).order_by(
            "data_inserarii", "id"
        )
    )
    if candidat is not None:
        inlocuit = False
        for i, row in enumerate(rows):
            if candidat.pk is not None and row.pk == candidat.pk:
                rows[i] = candidat
                inlocuit = True
                break
        if not inlocuit:
            rows.append(candidat)

    from incasari.models import IncasariModel

    incasari_totale = D(IncasariModel.get_total_incasari(an))
    amortizari = total_amortizari(an)

    rezultate = {}
    salarii = D(0)
    sociale_deja = D(0)
    contrib_deja = D(0)
    plafon_deja = {cod: D(0) for cod in _EUR_CAP_CODURI}
    burse_deja = D(0)
    altele_deduse = D(0)  # non-protocol, non-burse, non-mijloc fix

    parametri = get_parametri(an)
    procente = parametri["deductibilitati"]["procente"]
    plafoane_eur = parametri["deductibilitati"]["plafoane_eur"]
    coduri_baza = (
        Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value,
        Deductibilitate.DEDUCTIBILA_PARTIAL_BURSE.value,
    )

    for c in rows:
        cod = c.deductibila
        if cod in coduri_baza:
            continue
        base = D(suma_in_ron(c))
        tva = D(tva_autolichidata(c) or 0)

        if cod in MIJLOC_FIX_CODURI or cod in (
            Deductibilitate.DEDUCTIBILA_INTEGRAL.value,
            Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII.value,
            Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR.value,
        ):
            deducere = D(base + tva)
            if cod == Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII.value:
                salarii += deducere
        elif cod == Deductibilitate.DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI.value:
            deducere = D(base * D(str(procente["auto"])) + tva)
        elif cod == Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE.value:
            admis = D(salarii * D(str(procente["sociale"])))
            if sociale_deja + base > admis:
                raise _eroare_plafon(admis - sociale_deja)
            deducere = base
            sociale_deja += deducere
        elif (
            cod
            == Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG.value
        ):
            admis = D(incasari_totale * D(str(procente["contributii_obligatorii"])))
            if contrib_deja + base > admis:
                raise _eroare_plafon(admis - contrib_deja)
            deducere = base
            contrib_deja += deducere
        elif cod in _EUR_CAP_CODURI:
            euro_in_ron = to_ron(
                plafoane_eur[_EUR_CAP_CODURI[cod]], "EUR", c.data_inserarii
            )
            if plafon_deja[cod] + base > euro_in_ron:
                raise _eroare_plafon(euro_in_ron - plafon_deja[cod])
            deducere = base
            plafon_deja[cod] += deducere
        else:
            deducere = base

        rezultate[c.pk] = deducere
        if not mijloc_fix(c):
            altele_deduse += deducere

    # Baza de calcul (art. 68 alin. 6): venitul brut minus cheltuielile
    # deductibile, cu exceptia burselor private si a protocolului.
    baza_calcul = incasari_totale - altele_deduse - amortizari
    admis_protocol = D(baza_calcul * D(str(procente["protocol"])))
    admis_burse = D(baza_calcul * D(str(procente["burse_private"])))

    protocol_deja = D(0)
    for c in rows:
        cod = c.deductibila
        if cod not in coduri_baza:
            continue
        base = D(suma_in_ron(c))
        if cod == Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value:
            if protocol_deja + base > admis_protocol:
                raise _eroare_plafon(admis_protocol - protocol_deja)
            protocol_deja += base
        else:
            if burse_deja + base > admis_burse:
                raise _eroare_plafon(admis_burse - burse_deja)
            burse_deja += base
        rezultate[c.pk] = base

    if candidat is None:
        _CACHE[an] = (rev, rezultate)
    return rezultate


def deducere_in_ron(c):
    an = c.data_inserarii.year if c.data_inserarii else timezone.now().year
    return calculeaza_deduceri_anului(an).get(c.pk)


def valideaza(c):
    """Validare completa, apelata din model.clean()/save()."""
    # Completaza campurile cerute pentru taxarea inversa.
    if este_taxare_inversa(c):
        if not c.furnizor_denumire:
            raise ValidationError(
                _(
                    "Pentru servicii din UE/non-UE trebuie completata denumirea furnizorului."
                )
            )
        if not c.furnizor_tara:
            raise ValidationError(
                _("Pentru servicii din UE/non-UE trebuie selectata tara furnizorului.")
            )
        if este_ue(c) and not c.furnizor_cod_fiscal:
            raise ValidationError(
                _(
                    "Pentru servicii din UE trebuie completat codul TVA al furnizorului (ex. ATU77164426)."
                )
            )
        if este_ue(c):
            cod = (c.furnizor_cod_fiscal or "").strip().upper()
            if not cod.startswith(c.furnizor_tara.upper()):
                raise ValidationError(
                    _(
                        "Codul TVA '{}' nu incepe cu prefixul tarii furnizorului ({}). Verifica factura.".format(
                            cod, c.furnizor_tara
                        )
                    )
                )
        if not c.numar_factura:
            raise ValidationError(
                _("Pentru servicii din UE/non-UE trebuie completat numarul facturii.")
            )

    if c.deductibila in MIJLOC_FIX_CODURI:
        clasificare(c)
        if not c.data_punerii_in_functiune:
            raise ValidationError(
                _("Pentru un mijloc fix trebuie completata data punerii in functiune.")
            )

    an = c.data_inserarii.year if c.data_inserarii else timezone.now().year
    calculeaza_deduceri_anului(an, candidat=c)


# --- totaluri pentru dashboard/registre -------------------------------------


def get_total_cheltuieli(an):
    deduceri = calculeaza_deduceri_anului(an)
    total = D(0)
    for c in CheltuialaModel.objects.filter(data_inserarii__year=an):
        if not mijloc_fix(c):
            total += D(deduceri.get(c.pk) or 0)
    return rotund2(total + total_amortizari(an))


def get_total_cheltuieli_pe_luni(an):
    deduceri = calculeaza_deduceri_anului(an)
    rezultat = []
    for luna in range(1, 13):
        datetime.date(an, luna, 1)
        total = D(0)
        for c in CheltuialaModel.objects.filter(
            data_inserarii__year=an, data_inserarii__month=luna
        ):
            if not mijloc_fix(c):
                total += D(deduceri.get(c.pk) or 0)
        for c in CheltuialaModel.objects.filter(q_mijloc_fix()):
            if luna in luni_amortizare_active_in_an(c, an) and amortizare_lunara(c):
                total += D(amortizare_lunara(c))
        rezultat.append(total)
    return rezultat
