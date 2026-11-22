"""Motorul de calcul pentru D301, D390 VIES si Jurnalul de cumparari.

Reguli (conform ghidului din stocare/completare-declaratii-tva):
- Servicii UE:     D301 sectiunea 4 + sectiunea 4.1 (tip_operatie 5) + D390 tip S,
                   declarate cu codul special de TVA intracomunitar (art. 317).
- Servicii non-UE: doar D301 sectiunea 4, declarate cu CIF-ul normal al PFA-ului.
- Baza si TVA: 2 zecimale; baza D390: rotunjita la intreg (lei).
- TVA = baza x cota standard (21%); total document jurnal = baza + TVA.
- Termen depunere/plata: 25 inclusiv a lunii urmatoare exigibilitatii.
"""

import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from cheltuieli.models import CheltuialaModel, TipAchizitie
from setari.models import SetariModel
from utils.tari import denumire_tara


COD_REFERINTA_JURNAL = "15-16"
DENUMIRE_REFERINTA_JURNAL = (
    "Cumparari pt. care cumparatorul este obligat la plata TVA art. 307"
)


def round2(value) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def round_lei_intreg(value) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def termen_depunere(anul: int, luna: int) -> datetime.date:
    """25 inclusiv a lunii urmatoare celei de raportare."""
    if luna == 12:
        return datetime.date(anul + 1, 1, 25)
    return datetime.date(anul, luna + 1, 25)


def get_cheltuieli_taxare_inversa(anul: int, luna: int | None = None):
    """Cheltuielile cu taxare inversa din luna (sau anul) de raportare.
    Luna de raportare este data facturii (exigibilitatea), cu fallback pe data cheltuielii."""
    query = Q(tip_achizitie__in=[TipAchizitie.SERVICII_UE, TipAchizitie.SERVICII_NON_UE])

    if luna is not None:
        query &= (
            Q(data_facturii__year=anul, data_facturii__month=luna)
            | Q(data_facturii__isnull=True, data_inserarii__year=anul, data_inserarii__month=luna)
        )
    else:
        query &= (
            Q(data_facturii__year=anul)
            | Q(data_facturii__isnull=True, data_inserarii__year=anul)
        )

    return CheltuialaModel.objects.filter(query).order_by(
        "data_facturii", "data_inserarii", "id"
    )


def get_luni_cu_taxare_inversa(anul: int) -> list[int]:
    luni = set()
    for cheltuiala in get_cheltuieli_taxare_inversa(anul):
        data = cheltuiala.data_facturii or cheltuiala.data_inserarii
        if data:
            luni.add(data.month)
    return sorted(luni)


def _data_document(cheltuiala) -> datetime.date:
    return cheltuiala.data_facturii or cheltuiala.data_inserarii


def _rand_d301(cheltuiala, nr_crt: int, tip_operatie: str) -> dict:
    data = _data_document(cheltuiala)
    return {
        "nr_crt": nr_crt,
        "tip_operatie": tip_operatie,
        "nr_doc": cheltuiala.numar_factura or "",
        "data_doc": data.strftime("%d.%m.%Y") if data else "",
        "val_valuta": cheltuiala.suma,
        "tip_valuta": cheltuiala.valuta,
        "curs_valutar": cheltuiala.curs_bnr_aplicat,
        "baza": cheltuiala.baza_in_lei,
        "tva": cheltuiala.tva_autolichidata,
        "este_ue": cheltuiala.este_ue,
        "furnizor": cheltuiala.furnizor_denumire or "",
    }


def _cif_d301(setari: SetariModel, cheltuieli) -> tuple[str, bool]:
    """CIF-ul declarat in D301: codul special de TVA intracomunitar daca exista
    (declaratia se depune pe art. 317), altfel CIF-ul normal.
    Returneaza (cif, are_ue)."""
    are_ue = any(c.este_ue for c in cheltuieli)
    if setari.cod_tva_intracomunitar:
        return setari.cod_tva_intracomunitar.strip().upper().removeprefix("RO"), are_ue
    return setari.get_cif_pentru_achizitie(este_ue=False), are_ue


def calculeaza_d301(anul: int, luna: int, setari: SetariModel | None = None) -> dict | None:
    """Snapshot-ul D301 pentru o luna: toate operatiunile cu taxare inversa
    in sectiunea 4, iar cele din UE si in sectiunea 4.1 (tip_operatie 5).
    Returneaza None daca nu exista operatiuni."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))
    if not cheltuieli:
        return None

    randuri = []
    for idx, cheltuiala in enumerate(cheltuieli, start=1):
        randuri.append(_rand_d301(cheltuiala, idx, "4"))
        if cheltuiala.este_ue:
            randuri.append(_rand_d301(cheltuiala, idx, "5"))

    randuri4 = [r for r in randuri if r["tip_operatie"] == "4"]
    randuri5 = [r for r in randuri if r["tip_operatie"] == "5"]

    baza4 = round2(sum(r["baza"] for r in randuri4))
    tva4 = round2(sum(r["tva"] for r in randuri4))
    baza5 = round2(sum(r["baza"] for r in randuri5))
    tva5 = round2(sum(r["tva"] for r in randuri5))

    cif, are_ue = _cif_d301(setari, cheltuieli)

    return {
        "anul": anul,
        "luna": luna,
        "cif": cif,
        "are_ue": are_ue,
        "randuri": randuri,
        "baza4": baza4,
        "tva4": tva4,
        "baza5": baza5,
        "tva5": tva5,
        "total_de_plata": tva4,
        "termen": termen_depunere(anul, luna),
    }


def calculeaza_d390(anul: int, luna: int, setari: SetariModel | None = None) -> dict | None:
    """Snapshot-ul D390 VIES: doar achizitiile de servicii din UE (tip S),
    grupate pe operator intracomunitar, baza rotunjita la intreg.
    Codul operatorului se scrie fara prefixul de tara (tara e coloana separata)."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    cheltuieli_ue = [
        c for c in get_cheltuieli_taxare_inversa(anul, luna) if c.este_ue
    ]
    if not cheltuieli_ue:
        return None

    operatori = {}
    for cheltuiala in cheltuieli_ue:
        cod_complet = (cheltuiala.furnizor_cod_fiscal or "").strip().upper()
        tara = (cheltuiala.furnizor_tara or "").strip().upper()
        cod_operator = cod_complet.removeprefix(tara)
        cheie = (tara, cod_operator, (cheltuiala.furnizor_denumire or "").strip().upper())
        operatori.setdefault(cheie, 0)
        operatori[cheie] += cheltuiala.baza_in_lei or 0

    randuri = []
    for idx, ((tara, cod_operator, denumire), baza) in enumerate(operatori.items(), start=1):
        randuri.append(
            {
                "nr_crt": idx,
                "tip": "S",
                "tara": tara,
                "tara_denumire": denumire_tara(tara),
                "cod_operator": cod_operator,
                "denumire_operator": denumire,
                "baza": round_lei_intreg(baza),
            }
        )

    total_baza = sum(r["baza"] for r in randuri)

    return {
        "anul": anul,
        "luna": luna,
        "cif": setari.get_cif_pentru_achizitie(este_ue=True),
        "randuri": randuri,
        "nr_operatori": len(randuri),
        "bazaS": total_baza,
        "total_baza": total_baza,
        "total_de_plata": 0,  # D390 este informativa, fara plata
        "termen": termen_depunere(anul, luna),
    }


def calculeaza_jurnal_cumparari(anul: int, luna: int | None = None) -> dict | None:
    """Jurnalul pentru cumparari (registru contabil, nu declaratie):
    toate facturile cu taxare inversa, cod referinta 15-16,
    total document = baza + TVA autolichidata."""
    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))
    if not cheltuieli:
        return None

    randuri = []
    for idx, cheltuiala in enumerate(cheltuieli, start=1):
        data = _data_document(cheltuiala)
        baza = cheltuiala.baza_in_lei or 0
        tva = cheltuiala.tva_autolichidata or 0
        randuri.append(
            {
                "nr_crt": idx,
                "data_doc": data.strftime("%d.%m.%Y") if data else "",
                "nr_doc": cheltuiala.numar_factura or "",
                "furnizor_denumire": cheltuiala.furnizor_denumire or "",
                "furnizor_cod_fiscal": cheltuiala.furnizor_cod_fiscal or "",
                "total_document": round2(baza + tva),
                "baza": round2(baza),
                "tva": round2(tva),
                "cod_referinta": COD_REFERINTA_JURNAL,
            }
        )

    return {
        "anul": anul,
        "luna": luna,
        "randuri": randuri,
        "total_document": round2(sum(r["total_document"] for r in randuri)),
        "total_baza": round2(sum(r["baza"] for r in randuri)),
        "total_tva": round2(sum(r["tva"] for r in randuri)),
    }


def get_observatii_declaratie(anul: int, luna: int, setari: SetariModel | None = None) -> list[str]:
    """Atentionari inainte de generare/depunere."""
    setari = setari or SetariModel.objects.first()
    observatii = []
    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))

    if any(c.este_ue for c in cheltuieli) and not (setari and setari.cod_tva_intracomunitar):
        observatii.append(
            "Ai facturi din UE dar nu ai completat codul special de TVA intracomunitar in Setari. "
            "Declaratiile se vor genera cu CIF-ul normal, ceea ce poate fi gresit."
        )
    if cheltuieli and not (setari and setari.cont_iban_trezoreria):
        observatii.append(
            "Nu ai completat IBAN-ul trezoreriei in Setari. "
            "TVA-ul din D301 se plateste in contul 20A100101 al trezoreriei de domiciliul fiscal."
        )
    return observatii
