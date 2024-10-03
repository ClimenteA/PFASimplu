import os
from zipfile import ZipFile
from cheltuieli.models import CheltuialaModel
from fpdf_table import PDFTable, Align
from core.settings import MEDIA_ROOT, get_extracts_path, get_font_path



def create_fisa_mijloc_fix_pdf(db_id: int, nr_inventar: int):

    inv = CheltuialaModel.objects.filter(id=db_id).first()

    fileid = os.path.basename(inv.fisier.path).split("_")[0]

    fel_document = f"{fileid} {inv.nume_cheltuiala}"

    pdf = PDFTable()

    pdf.add_fonts_custom(
        font_name="arial", 
        font_extension="ttf", 
        font_dir=get_font_path(), 
        set_default=True
    )

    # Date identificare factura
    pdf.table_header(["FIŞA MIJLOCULUI FIX"], align=Align.L)
    pdf.table_row([''])
    pdf.table_row(['Nr. Inventar: ', str(nr_inventar)])
    pdf.table_row(['Fel, serie, nr. data document provenienţă: ', fel_document])
    pdf.table_row(['Valoare de inventar: ', str(inv.suma_in_ron)])
    pdf.table_row(['Amortizare lunară: ', str(inv.amortizare_lunara)])
    pdf.table_row(['Denumirea mijlocului fix şi caracteristici tehnice: ', "Detaliate in factura/bon."])
    pdf.table_row(['Accesorii: ', "Detaliate in factura/bon."])
    pdf.table_row(['Grupa: ', inv.grupa], option='responsive')
    pdf.table_row(['Codul de clasificare: ', inv.cod_de_clasificare])
    pdf.table_row(['Anul dării în folosinţă: ', str(inv.anul_darii_in_folosinta)])
    pdf.table_row(['Luna dării în folosinţă: ', str(inv.luna_darii_in_folosinta)])
    pdf.table_row(['Anul amortizării complete: ', str(inv.anul_amortizarii_complete)])
    pdf.table_row(['Luna amortizării complete: ', str(inv.luna_amortizarii_complete)])
    pdf.table_row(['Durata normală de funcţionare: ', inv.durata_normala_de_functionare])
    pdf.table_row(['Cota de amortizare: ', str(inv.cota_de_amortizare)])

    pdf.table_row([''])
    
    width_cols = pdf.table_cols(1, 3, 3.5, 0.5, 1, 1, 1, 1)
    pdf.set_font(pdf.font, "B", pdf.text_normal_size)

    mutari_header = [
        "Nr.inventar (de la număr la număr)",
        "Documentul (data, felul, numărul)",
        "Operaţiunile care privesc mişcarea, creşterea sau diminuarea valorii mijlocului fix",
        "Buc.",
        "Debit",
        "Credit",
        "Sold",
        'Soldul contului 105 "Rezerve din reevaluare"'
    ]

    pdf.table_row(mutari_header, width_cols, option='responsive')
    pdf.set_font(pdf.font, "", pdf.text_normal_size)
    
    empty_rows = [""]*len(mutari_header)
    for _ in range(20): 
        pdf.table_row(empty_rows, width_cols)

    save_pdf_path = os.path.join(MEDIA_ROOT, "fisa_mijloc_fix.pdf")
    pdf.output(save_pdf_path)

    extracts_folder = get_extracts_path()

    files = [save_pdf_path, inv.fisier.path]
    zip_filepath = os.path.join(extracts_folder, f"{fel_document}.zip")
    with ZipFile(zip_filepath, "w") as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))

    return zip_filepath

