from xhtml2pdf import pisa

pisa.showLogging()


def create_pdf_from_html(html_str_or_path: str, pdf_output_path: str):

    with open(pdf_output_path, "w+b") as file:
        pisa_status = pisa.CreatePDF(html_str_or_path, dest=file)           
        if pisa_status.err:
            raise Exception("Nu am putut crea pdf-ul")

    return pdf_output_path

