import os
import glob
import json
import pandas as pd
from documente.models import DocumenteModel, TipDocument
from incasari.models import IncasariModel
from cheltuieli.models import CheltuialaModel
from setari.models import SetariModel
from django.core.files import File
from django.utils import timezone
from datetime import datetime
import numpy as np


class DataImportV2:

    def insert_date_pfa(self):

        df = pd.read_csv(os.path.join("stocare", "Setari.csv"))
        df.fillna("", inplace=True)

        data = df.to_records("dict")[0]

        instance = SetariModel(
            nume = data["nume"],
            localitate = data["localitate"],
            adresa = data["adresa"],
            nr_reg_com = data["nr_reg_com"],
            cif = data["cif"],
            email = data["email"],
            telefon = data["telefon"],
            iban = data["iban"],
            caen_principal = data["caen_principal"],
            caen_secondar_1 = data["caen_secondar_1"],
            caen_secondar_2 = data["caen_secondar_2"],
            caen_secondar_3 = data["caen_secondar_3"],
            caen_secondar_4 = data["caen_secondar_4"],
            caen_secondar_5 = data["caen_secondar_5"],
        )

        instance.save()

    def insert_incasari(self):
        # TODO
        incasare = IncasariModel(
            suma=r["Suma Incasata"],
            tip_tranzactie=r["Tip Tranzactie"],
            data_inserarii=data_inserarii,
            fisier=File(f, name=os.path.basename(r["Cale Fisier"])),
        )

        incasare.save()

        records = self.get_incasari_records()

        for r in records:
            with open(r["Cale Fisier"], "rb") as f:

                naive_datetime = datetime.strptime(r["Data"], "%Y-%m-%d")
                data_inserarii = timezone.make_aware(naive_datetime)

                incasare = IncasariModel(
                    suma=r["Suma Incasata"],
                    tip_tranzactie=r["Tip Tranzactie"],
                    data_inserarii=data_inserarii,
                    fisier=File(f, name=os.path.basename(r["Cale Fisier"])),
                )
                incasare.save()

    def insert_cheltuieli(self):

        df = pd.read_csv(os.path.join("stocare", "Cheltuiala.csv"))
        df = df.replace({np.nan: None})

        for record in df.to_dict('records'):

            data_punerii_in_functiune = None
            if record['data_punerii_in_functiune']:
                naive_datetime = datetime.strptime(record['data_punerii_in_functiune'], "%Y-%m-%d")
                data_punerii_in_functiune = timezone.make_aware(naive_datetime)

            data_amortizarii_complete = None
            if record['data_amortizarii_complete']:
                naive_datetime = datetime.strptime(record['data_amortizarii_complete'], "%Y-%m-%d")
                data_amortizarii_complete = timezone.make_aware(naive_datetime)

            data_inceperii_amortizarii = None
            if record['data_inceperii_amortizarii']:
                naive_datetime = datetime.strptime(record['data_inceperii_amortizarii'], "%Y-%m-%d")
                data_inceperii_amortizarii = timezone.make_aware(naive_datetime)

            incasare = CheltuialaModel(
                suma_in_ron=record['suma_in_ron'],
                suma=record['suma'],
                valuta=record['valuta'],
                tip_tranzactie=record['tip_tranzactie'],
                data_inserarii=record['data_inserarii'],
                fisier=record['fisier'],
                actualizat_la=record['actualizat_la'],
                nume_cheltuiala=record['nume_cheltuiala'],
                deductibila=record['deductibila'],
                deducere_in_ron=record['deducere_in_ron'],
                obiect_de_inventar=record['obiect_de_inventar'],
                mijloc_fix=record['mijloc_fix'],
                cod_de_clasificare=record['cod_de_clasificare'],
                grupa=record['grupa'],
                data_punerii_in_functiune=data_punerii_in_functiune,
                data_amortizarii_complete=data_amortizarii_complete,
                data_inceperii_amortizarii=data_inceperii_amortizarii,
                durata_normala_de_functionare=record['durata_normala_de_functionare'],
                anul_darii_in_folosinta=record['anul_darii_in_folosinta'],
                luna_darii_in_folosinta=record['luna_darii_in_folosinta'],
                anul_amortizarii_complete=record['anul_amortizarii_complete'],
                luna_amortizarii_complete=record['luna_amortizarii_complete'],
                ani_amortizare=record['ani_amortizare'],
                amortizare_lunara=record['amortizare_lunara'],
                cota_de_amortizare=record['cota_de_amortizare'],
                scos_din_uz=record['scos_din_uz'],
                modalitate_iesire_din_uz=record['modalitate_iesire_din_uz'],
                data_iesirii_din_uz=record['data_iesirii_din_uz'],
                document_justificativ_iesire_din_uz=record['document_justificativ_iesire_din_uz'],
            )
    
            incasare.save()


    def insert_documente(self):
        # TODO
        
        tipdocmap = {
            "Declaratie unica (212)": TipDocument.DECLARATIE_UNICA_212,
            "Dovada incarcare Declaratie 212": TipDocument.DECLARATIE_UNICA_212_DOVADA_INCARCARE,
            "Dovada plata impozite": TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE,
        }

        documente_path = os.path.join(self.account_path, "declaratii")
        for filepath in glob.glob(f"{documente_path}/**/*", recursive=True):
            if not os.path.isfile(filepath):
                continue
            if not filepath.endswith(".json"):
                continue

            with open(filepath, "r") as f:
                m = json.load(f)

            with open(m["cale_document"], "rb") as f:
                instance = DocumenteModel(
                    tip_document=tipdocmap.get(
                        m["tip_document"], TipDocument.DOCUMENT_UTIL
                    ),
                    mentiuni=m["tip_document"],
                    document_pentru_anul=m["pentru_anul"],
                    fisier=File(f, name=os.path.basename(m["cale_document"])),
                )

                instance.save()
