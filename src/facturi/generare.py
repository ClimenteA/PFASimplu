"""Generarea PDF-ului si a XML-ului e-factura.

Generarea nu mai are loc in `FacturaModel.save()`: save() pastreaza doar
datele, iar fisierele se produc la crearea facturii (vezi FacturiView.post).
"""

import os

from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from core.settings import get_media_path
from setari.models import SetariModel
from utils.decimale import format_suma
from utils.valuta import TipTranzactie

from .models import FacturaModel, TipFactura, creeaza_factura_pdf

_COD_PLATA_XML = {
    TipTranzactie.BANCAR.value: "42",
    TipTranzactie.NUMERAR.value: "10",
}


def construieste_context(factura: FacturaModel) -> dict:
    furnizor = SetariModel.objects.first()
    if not furnizor:
        raise ValueError("Introdu mai intai datele PFA-ului in Setari!")

    return {
        "tip_factura": factura.tip_factura,
        "valuta": factura.valuta,
        "show_iban_furnizor": factura.tip_tranzactie == TipTranzactie.BANCAR.value,
        "serie": factura.serie,
        "numar": str(factura.numar),
        "serie_numar": f"{factura.serie}-{factura.numar}",
        "data_emitere": factura.data_emitere.isoformat(),
        "data_scadenta": factura.data_scadenta.isoformat(),
        "nota": factura.nota,
        "adresa_furnizor": furnizor.adresa,
        "localitate_furnizor": FacturaModel.get_localitate(furnizor.localitate),
        "cod_judet_furnizor": FacturaModel.get_cod_judet(furnizor.localitate),
        "cif_furnizor": furnizor.cif,
        "nr_reg_com_furnizor": furnizor.nr_reg_com,
        "nume_furnizor": furnizor.nume,
        "email_furnizor": furnizor.email,
        "telefon_furnizor": furnizor.telefon,
        "iban_furnizor": furnizor.get_iban_pentru_valuta(factura.valuta),
        "iban_client": "",
        "adresa_client": factura.adresa,
        "localitate_client": FacturaModel.get_localitate(factura.localitate),
        "cod_judet_client": FacturaModel.get_cod_judet(factura.localitate),
        "nume_client": factura.nume,
        "cif_client": str(factura.cif),
        "nr_reg_com_client": factura.nr_reg_com,
        "email_client": factura.email,
        "telefon_client": factura.telefon,
        "cod_modalitate_plata": _COD_PLATA_XML.get(
            factura.tip_tranzactie, factura.tip_tranzactie
        ),
        "total_de_plata": format_suma(factura.total_de_plata),
        "produse_sau_servicii": factura.produse_sau_servicii,
    }


def genereaza_documente(factura: FacturaModel):
    context = construieste_context(factura)

    if factura.tip_factura == TipFactura.E_FACTURA.value:
        xml_content = render_to_string("efactura.xml", context)
        factura.fisier_efactura_xml.save(
            "efactura.xml", ContentFile(xml_content), save=False
        )

    save_pdf_path = os.path.join(get_media_path(), f"factura_{factura.id}.pdf")
    creeaza_factura_pdf(context, save_pdf_path)
    with open(save_pdf_path, "rb") as pdf:
        factura.fisier_factura_pdf.save(
            f"factura_{factura.serie}-{factura.numar}.pdf",
            ContentFile(pdf.read()),
            save=False,
        )

    factura.save(update_fields=["fisier_efactura_xml", "fisier_factura_pdf"])
    return factura
