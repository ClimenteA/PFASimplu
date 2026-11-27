"""Motorul de calcul pentru D301, D390 VIES si Jurnalul de cumparari.

Reguli (conform ghidului din stocare/completare-declaratii-tva):
- Servicii UE:     D301 sectiunea 4 + sectiunea 4.1 (tip_operatie 5) + D390 tip S,
                   declarate cu codul special de TVA intracomunitar (art. 317) din Setari.
- Servicii non-UE: doar D301 sectiunea 4 (fara D390), declarate cu CIF-ul normal din Setari.
- Incasari din UE (facturi cu Client UE): doar D390 tip P (prestari), pe codul art. 317,
  fara D301 si fara TVA de plata (clientul datoreaza taxa in statul lui membru).
- Intr-o luna cu ambele tipuri se genereaza doua D301 separate, fiecare pe codul ei.
- Baza si TVA: 2 zecimale; baza D390: rotunjita la intreg (lei).
- TVA = baza x cota standard de 21% (doar pentru furnizori straini); total document jurnal = baza + TVA.
- Termen depunere/plata: 25 inclusiv a lunii urmatoare exigibilitatii.
"""

import datetime
import os
from decimal import Decimal

from django.db.models import Q

from cheltuieli.calcul import q_taxare_inversa
from cheltuieli.models import CheltuialaModel
from facturi.models import FacturaModel
from setari.models import SetariModel
from utils.cursuri import to_ron
from utils.decimale import D, rotund2, rotund_intreg, suma
from utils.tari import TARI, denumire_tara, este_tara_ue

COD_REFERINTA_JURNAL = "15-16"
DENUMIRE_REFERINTA_JURNAL = (
    "Cumparari pt. care cumparatorul este obligat la plata TVA art. 307"
)


def round2(value) -> Decimal:
    """Suma finala, 2 zecimale, rotunjire .5 in sus (alias catre rotund2)."""
    return rotund2(value)


def round_lei_intreg(value) -> int:
    """Rotunjire la intreg, .5 in sus (alias catre rotund_intreg)."""
    return rotund_intreg(value)


def termen_depunere(anul: int, luna: int) -> datetime.date:
    """25 inclusiv a lunii urmatoare celei de raportare."""
    if luna == 12:
        return datetime.date(anul + 1, 1, 25)
    return datetime.date(anul, luna + 1, 25)


def get_cheltuieli_taxare_inversa(anul: int, luna: int | None = None):
    """Cheltuielile cu taxare inversa din luna (sau anul) de raportare.
    Luna de raportare este data facturii (exigibilitatea), cu fallback pe data cheltuielii."""
    query = q_taxare_inversa()

    if luna is not None:
        query &= Q(data_facturii__year=anul, data_facturii__month=luna) | Q(
            data_facturii__isnull=True,
            data_inserarii__year=anul,
            data_inserarii__month=luna,
        )
    else:
        query &= Q(data_facturii__year=anul) | Q(
            data_facturii__isnull=True, data_inserarii__year=anul
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


def _snapshot_d301(
    cheltuieli: list, anul: int, luna: int, cif: str, are_ue: bool
) -> dict:
    """Snapshot-ul unei declaratii D301 pentru un grup de facturi (acelasi cod).
    Toate operatiunile intra in sectiunea 4, iar cele din UE si in sectiunea 4.1
    (tip_operatie 5)."""
    randuri = []
    for idx, cheltuiala in enumerate(cheltuieli, start=1):
        randuri.append(_rand_d301(cheltuiala, idx, "4"))
        if cheltuiala.este_ue:
            randuri.append(_rand_d301(cheltuiala, idx, "5"))

    randuri4 = [r for r in randuri if r["tip_operatie"] == "4"]
    randuri5 = [r for r in randuri if r["tip_operatie"] == "5"]

    baza4 = round2(suma([r["baza"] for r in randuri4]))
    tva4 = round2(suma([r["tva"] for r in randuri4]))
    baza5 = round2(suma([r["baza"] for r in randuri5]))
    tva5 = round2(suma([r["tva"] for r in randuri5]))

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


def calculeaza_d301_lista(
    anul: int, luna: int, setari: SetariModel | None = None
) -> list[dict]:
    """Declaratiile D301 ale lunii, separate pe codul de identificare folosit:
    - facturile din UE se declara cu codul special de TVA intracomunitar (art. 317);
    - facturile din afara UE se declara cu CIF-ul normal al PFA-ului.
    Intr-o luna cu ambele tipuri (si coduri diferite) rezulta doua D301."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return []

    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))
    if not cheltuieli:
        return []

    cif_ue = setari.get_cif_pentru_achizitie(este_ue=True)
    cif_non_ue = setari.get_cif_pentru_achizitie(este_ue=False)

    ue = [c for c in cheltuieli if c.este_ue]
    non_ue = [c for c in cheltuieli if not c.este_ue]

    declaratii = []
    if ue:
        declaratii.append(_snapshot_d301(ue, anul, luna, cif_ue, are_ue=True))
    if non_ue:
        if cif_non_ue == cif_ue and declaratii:
            # Acelasi cod (nu exista cod special art. 317): o singura D301,
            # cu toate facturile in sectiunea 4.
            declaratii = [_snapshot_d301(cheltuieli, anul, luna, cif_ue, are_ue=True)]
        else:
            declaratii.append(
                _snapshot_d301(non_ue, anul, luna, cif_non_ue, are_ue=False)
            )
    return declaratii


def calculeaza_d301(
    anul: int, luna: int, setari: SetariModel | None = None
) -> dict | None:
    """Prima declaratie D301 a lunii (sau None daca nu exista operatiuni)."""
    declaratii = calculeaza_d301_lista(anul, luna, setari)
    return declaratii[0] if declaratii else None


def calculeaza_d390(
    anul: int, luna: int, setari: SetariModel | None = None
) -> dict | None:
    """Snapshot-ul D390 VIES: doar achizitiile de servicii din UE (tip S),
    grupate pe operator intracomunitar, baza rotunjita la intreg.
    Codul operatorului se scrie fara prefixul de tara (tara e coloana separata)."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    cheltuieli_ue = [c for c in get_cheltuieli_taxare_inversa(anul, luna) if c.este_ue]
    if not cheltuieli_ue:
        return None

    operatori = {}
    for cheltuiala in cheltuieli_ue:
        cod_complet = (cheltuiala.furnizor_cod_fiscal or "").strip().upper()
        tara = (cheltuiala.furnizor_tara or "").strip().upper()
        cod_operator = cod_complet.removeprefix(tara)
        cheie = (
            tara,
            cod_operator,
            (cheltuiala.furnizor_denumire or "").strip().upper(),
        )
        operatori.setdefault(cheie, Decimal(0))
        operatori[cheie] += D(cheltuiala.baza_in_lei or 0)

    randuri = []
    for idx, ((tara, cod_operator, denumire), baza) in enumerate(
        operatori.items(), start=1
    ):
        randuri.append(
            {
                "nr_crt": idx,
                "tip": "S",
                "tara": tara,
                "tara_denumire": denumire_tara(tara),
                "cod_operator": cod_operator,
                "denumire_operator": denumire,
                "baza": rotund_intreg(baza),
            }
        )

    total_baza = int(suma([r["baza"] for r in randuri]))

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


def get_facturi_ue(anul: int, luna: int | None = None):
    """Facturile emise catre clienti UE (bifa „Client UE") din luna/anul de
    raportare. Luna de raportare este data emiterii facturii (exigibilitatea
    TVA la client, prin taxare inversa in statul membru al acestuia)."""
    query = Q(client_ue=True)
    if luna is not None:
        query &= Q(data_emitere__year=anul, data_emitere__month=luna)
    else:
        query &= Q(data_emitere__year=anul)
    return FacturaModel.objects.filter(query).order_by("data_emitere", "id")


def get_luni_cu_facturi_ue(anul: int) -> list[int]:
    """Lunile cu facturi catre clienti UE, pentru filtrul din pagina Incasari."""
    return sorted(
        set(get_facturi_ue(anul).values_list("data_emitere__month", flat=True))
    )


def _operator_client(cif: str) -> tuple[str, str]:
    """Desparte codul TVA al clientului UE in tara (prefix ISO) si cod operator
    (fara prefix), asa cum se completeaza in D390."""
    cod = (cif or "").strip().upper()
    prefix = cod[:2]
    if TARI.get(prefix, ("", False))[1]:
        return prefix, cod[2:]
    return "", cod


def calculeaza_d390_incasari(
    anul: int, luna: int, setari: SetariModel | None = None
) -> dict | None:
    """D390 VIES pentru vanzarile/prestarile catre clienti UE (tip P), declarate
    pe codul special de TVA intracomunitar (art. 317), fara TVA de plata:
    - art. 325 alin. (1) lit. c) Cod fiscal: se declara prestarile de servicii
      cu locul in alt stat membru (art. 278 alin. (2)) catre persoane impozabile
      din UE, altele decat cele scutite de TVA in statul lor;
    - art. 325 alin. (3) lit. b), f): codul clientului si valoarea totala pe
      fiecare client in parte; baza in lei, rotunjita la intreg.
    Nu se depune D301: TVA-ul se datoreaza de client in statul sau membru."""
    setari = setari or SetariModel.objects.first()
    if not setari:
        return None

    facturi = list(get_facturi_ue(anul, luna))
    if not facturi:
        return None

    operatori = {}
    observatii = []
    for factura in facturi:
        tara, cod_operator = _operator_client(factura.cif)
        denumire = (factura.nume or "").strip().upper()
        cheie = (tara, cod_operator, denumire)
        # Conversia foloseste aceeasi sursa (BNR) ca restul aplicatiei, la data
        # emiterii facturii; precizia Decimal se pastreaza pana la rotunjirea finala.
        baza = D(to_ron(factura.total_de_plata, factura.valuta, factura.data_emitere))
        operatori.setdefault(cheie, Decimal(0))
        operatori[cheie] += baza

        numar = f"{factura.serie}-{factura.numar}"
        if not tara:
            observatii.append(
                f"Factura {numar}: codul clientului '{factura.cif}' nu are prefix de tara. "
                "Completeaza codul TVA cu prefixul tarii (ex. ATU77164426)."
            )
        elif not este_tara_ue(tara):
            observatii.append(
                f"Factura {numar}: codul clientului are prefixul {tara}, care nu este stat UE. "
                "D390 se depune doar pentru clienti din UE."
            )

    randuri = []
    for idx, ((tara, cod_operator, denumire), baza) in enumerate(
        operatori.items(), start=1
    ):
        randuri.append(
            {
                "nr_crt": idx,
                "tip": "P",
                "tara": tara,
                "tara_denumire": denumire_tara(tara) if tara else "?",
                "cod_operator": cod_operator,
                "denumire_operator": denumire,
                "baza": rotund_intreg(baza),
            }
        )

    total_baza = int(suma([r["baza"] for r in randuri]))
    if not setari.cod_tva_intracomunitar:
        observatii.append(
            "Ai facturi catre clienti UE dar nu ai completat codul special de TVA "
            "intracomunitar in Setari. Declaratia se va genera cu CIF-ul normal, "
            "ceea ce poate fi gresit."
        )

    return {
        "anul": anul,
        "luna": luna,
        "cif": setari.get_cif_pentru_achizitie(este_ue=True),
        "randuri": randuri,
        "nr_operatori": len(randuri),
        "nr_facturi": len(facturi),
        "bazaP": total_baza,
        "total_baza": total_baza,
        "total_de_plata": 0,  # D390 este informativa; TVA-ul il plateste clientul.
        "termen": termen_depunere(anul, luna),
        "observatii": observatii,
    }


def calculeaza_jurnal_vanzari(anul: int, luna: int | None = None) -> dict | None:
    """Jurnalul de vanzari (registru contabil, nu declaratie): facturile emise
    catre clienti UE, cu valoarea in lei si documentul justificativ."""
    facturi = list(get_facturi_ue(anul, luna))
    if not facturi:
        return None

    randuri = []
    for idx, factura in enumerate(facturi, start=1):
        _, cod_operator = _operator_client(factura.cif)
        baza = D(to_ron(factura.total_de_plata, factura.valuta, factura.data_emitere))
        incasare = getattr(factura, "incasare", None)
        data_incasare = (
            incasare.data_incasarii
            if incasare is not None and incasare.data_incasarii
            else None
        )
        randuri.append(
            {
                "nr_crt": idx,
                "data_doc": factura.data_emitere.strftime("%d.%m.%Y"),
                "nr_doc": f"{factura.serie}-{factura.numar}",
                "client_denumire": factura.nume or "",
                "client_cod_fiscal": cod_operator,
                "val_valuta": factura.total_de_plata,
                "tip_valuta": factura.valuta,
                "baza": rotund2(baza),
                "data_incasare": (
                    data_incasare.strftime("%d.%m.%Y") if data_incasare else ""
                ),
                "fisier": (
                    os.path.basename(factura.fisier_factura_pdf.path)
                    if factura.fisier_factura_pdf
                    else ""
                ),
            }
        )

    return {
        "anul": anul,
        "luna": luna,
        "randuri": randuri,
        "total_baza": rotund2(suma([r["baza"] for r in randuri])),
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
        baza = D(cheltuiala.baza_in_lei or 0)
        tva = D(cheltuiala.tva_autolichidata or 0)
        randuri.append(
            {
                "nr_crt": idx,
                "data_doc": data.strftime("%d.%m.%Y") if data else "",
                "nr_doc": cheltuiala.numar_factura or "",
                "furnizor_denumire": cheltuiala.furnizor_denumire or "",
                "furnizor_cod_fiscal": cheltuiala.furnizor_cod_fiscal or "",
                "total_document": rotund2(baza + tva),
                "baza": rotund2(baza),
                "tva": rotund2(tva),
                "cod_referinta": COD_REFERINTA_JURNAL,
                "fisier": os.path.basename(cheltuiala.fisier.path)
                if cheltuiala.fisier
                else "",
            }
        )

    return {
        "anul": anul,
        "luna": luna,
        "randuri": randuri,
        "total_document": rotund2(suma([r["total_document"] for r in randuri])),
        "total_baza": rotund2(suma([r["baza"] for r in randuri])),
        "total_tva": rotund2(suma([r["tva"] for r in randuri])),
    }


def get_observatii_declaratie(
    anul: int, luna: int, setari: SetariModel | None = None
) -> list[str]:
    """Atentionari inainte de generare/depunere."""
    setari = setari or SetariModel.objects.first()
    observatii = []
    cheltuieli = list(get_cheltuieli_taxare_inversa(anul, luna))

    if any(c.este_ue for c in cheltuieli) and not (
        setari and setari.cod_tva_intracomunitar
    ):
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
