import os
from pychromepdf import ChromePDF
from flaskwebgui import browser_path_dispacher, OPERATING_SYSTEM


def create_pdf_from_html(html_str_or_path: str, pdf_output_path: str):

    if os.path.exists(html_str_or_path):
        with open(html_str_or_path, "r") as f:
            html_str_or_path = f.read()
        
    cpdf = ChromePDF(browser_path_dispacher.get(OPERATING_SYSTEM)())
   
    with open(pdf_output_path,'w') as output_file:
        ok = cpdf.html_to_pdf(html_str_or_path, output_file)
        if not ok:
            raise Exception("Could not create PDF")
        
    return pdf_output_path
    