"""Asezarea facturii PDF, desenata direct cu pdf_oxide."""

import datetime

from utils.pdf import A4_INALTIME, LATIME_UTILA, MARGINE, DocumentPdf

# Latimile coloanelor din tabelul de produse (insumeaza LATIME_UTILA).
_COLOANE_PRODUSE = (
    (42, "left"),
    (174, "left"),
    (46, "center"),
    (60, "right"),
    (90, "right"),
    (69.88, "right"),
)

# Tabelul cu datele partilor: eticheta, furnizor, client.
_COLOANE_DETALII = (
    (96, "left"),
    (192.94, "left"),
    (192.94, "left"),
)

_LATIME_META = 230

# Eticheta notei, in limba facturii.
_ETICHETA_NOTA = {
    "e-factura": "Observatii",
    "factura-romana": "Observatii",
    "factura-engleza": "Notes",
    "factura-germana": "Anmerkungen",
    "factura-franceza": "Remarques",
    "factura-spaniola": "Observaciones",
    "factura-italiana": "Note",
    "factura-daneza": "Bemaerkninger",
    "factura-olandeza": "Opmerkingen",
    "factura-suedeza": "Anmaerkningar",
    "factura-finlandeza": "Huomautukset",
}


def _eticheta(eticheta: str) -> str:
    """Elimina repetitiile din etichetele bilingve: `Name/Name` -> `Name`."""

    if "/" not in eticheta:
        return eticheta
    limbi = list(dict.fromkeys(parte.strip() for parte in eticheta.split("/")))
    return "/".join(limbi)


def _data(valoare) -> str:
    """Data in format zz.ll.aaaa, din ISO sau dintr-un obiect data."""

    try:
        return datetime.date.fromisoformat(str(valoare)).strftime("%d.%m.%Y")
    except ValueError:
        return str(valoare)


def _randuri_detalii(data: dict) -> list[list[str]]:
    """Randurile tabelului furnizor/client, fara liniile complet goale."""

    perechi = [
        (data["nume_lang"], data["nume_furnizor"], data["nume_client"]),
        (
            data["nr_reg_com_lang"],
            data["nr_reg_com_furnizor"],
            data["nr_reg_com_client"],
        ),
        (data["cif_lang"], data["cif_furnizor"], data["cif_client"]),
        (data["adresa_lang"], data["adresa_furnizor"], data["adresa_client"]),
        (data["email_lang"], data["email_furnizor"], data["email_client"]),
        (data["telefon_lang"], data["telefon_furnizor"], data["telefon_client"]),
    ]
    if data.get("show_iban_furnizor") or data.get("iban_client"):
        perechi.append((data["iban_lang"], data["iban_furnizor"], data["iban_client"]))

    randuri = [
        [_eticheta(eticheta), str(furnizor or ""), str(client or "")]
        for eticheta, furnizor, client in perechi
    ]
    return [rand for rand in randuri if rand[1] or rand[2]]


def _randuri_produse(data: dict) -> list[list[str]]:
    """Randurile tabelului de produse, numerotate de la 1."""

    return [
        [
            str(index),
            str(produs["nume_produs_sau_serviciu"]),
            str(produs["cod_unitate"]),
            str(produs["numar_unitati"]),
            str(produs["pret_pe_unitate"]),
            str(produs["subtotal"]),
        ]
        for index, produs in enumerate(data["produse_sau_servicii"], start=1)
    ]


def scrie_factura_pdf(data: dict, cale_pdf: str) -> str:
    doc = DocumentPdf()
    titluri = data["header_date_client_furnizor"]

    # Titlul in stanga, datele facturii intr-un tabel mic in dreapta.
    doc.y -= 16
    doc.scrie_la(data["header_factura"], bold=True, marime=20)

    doc.y = A4_INALTIME - MARGINE
    doc.tabel(
        [
            ("", _LATIME_META - 102, "left"),
            ("", 102, "right"),
        ],
        [
            [_eticheta(eticheta), _data(valoare)]
            for eticheta, valoare in zip(
                data["header_date_factura"],
                (
                    data["serie"],
                    data["numar"],
                    data["data_emitere"],
                    data["data_scadenta"],
                ),
            )
        ],
        x=MARGINE + LATIME_UTILA - _LATIME_META,
        marime=8,
        antet=False,
        umplere_coloana=0,
    )
    doc.spatiu(14)

    # Furnizor si client, pe coloane separate, intr-un tabel de detalii.
    doc.tabel(
        [
            (titluri[0], _COLOANE_DETALII[0][0], "left"),
            (titluri[1], _COLOANE_DETALII[1][0], "left"),
            (titluri[2], _COLOANE_DETALII[2][0], "left"),
        ],
        _randuri_detalii(data),
        umplere_coloana=0,
    )
    doc.spatiu(14)

    # Tabelul de produse, cu antetul bilingv si litere mai mici pe antet.
    antet = [_eticheta(eticheta) for eticheta in data["header_produse_servicii"]]
    doc.tabel(
        [
            (antet[i], latime, aliniere)
            for i, (latime, aliniere) in enumerate(_COLOANE_PRODUSE)
        ],
        _randuri_produse(data),
        marime_antet=8,
    )
    doc.spatiu(12)

    doc.evidentiaza(
        f"{data['header_total_de_plata']} {data['total_de_plata']} {data['valuta']}",
        marime=10,
    )

    if data.get("nota"):
        doc.spatiu(12)
        doc.linie()
        doc.spatiu(6)
        eticheta_nota = _ETICHETA_NOTA.get(data.get("tip_factura"), "Observatii")
        doc.scrie(f"{eticheta_nota}: {data['nota']}", marime=9)

    subsol = (
        f"{data['header_factura']} {data['serie']}-{data['numar']}"
        " - {pagina} / {total}"
    )
    return doc.salveaza(cale_pdf, subsol=subsol)
