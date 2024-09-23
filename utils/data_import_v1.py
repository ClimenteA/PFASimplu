import os
import glob
import json
import pandas as pd
from documente.models import DocumenteModel, TipDocument
from incasari.models import IncasariModel
from cheltuieli.models import CheltuialaModel, Deductibilitate
from setari.models import SetariModel
from django.core.files import File
from django.utils import timezone
from datetime import datetime


class DataImportV1:

    def __init__(self):
        self.account_path = self.get_account_path()

    def get_account_path(self):
        accounts_path = os.path.join("stocare", "conturi")

        accounts_data = {}
        for account in os.listdir(accounts_path):
            with open(os.path.join(accounts_path, account), "r") as f:
                data = json.load(f)
            accounts_data[account.replace(".json", "")] = data

        account_paths = [
            os.path.join("stocare", account_key) for account_key in accounts_data.keys()
        ]
        account_paths = [p for p in account_paths if os.path.exists(p)]
        if len(account_paths) != 1:
            raise Exception(
                f"Aplicatia poate lucra doar cu un cont. Sterge unul folderele din stocare: {', '.join(list(accounts_data.keys()))}."
            )

        return account_paths[0]

    def get_furnizor_data(self):
        furnizor_path = os.path.join(self.account_path, "furnizor.json")
        with open(furnizor_path, "r") as f:
            furnizor_data = json.load(f)
        return furnizor_data

    def get_incasari_records(self):
        incasari_csv_paths = [
            os.path.join(self.account_path, p)
            for p in os.listdir(self.account_path)
            if p.endswith("_incasari.csv")
        ]
        dfs = [pd.read_csv(f) for f in incasari_csv_paths]
        dfs = [df for df in dfs if not df.empty]
        df_incasari = pd.concat(dfs, ignore_index=True)
        return df_incasari.to_dict("records")

    def get_cheltuieli_records(self):
        cheltuieli_csv_paths = [
            os.path.join(self.account_path, p)
            for p in os.listdir(self.account_path)
            if p.endswith("_cheltuieli.csv")
        ]
        dfs = [pd.read_csv(f) for f in cheltuieli_csv_paths]
        dfs = [df for df in dfs if not df.empty]
        df_cheltuieli = pd.concat(dfs, ignore_index=True)
        return df_cheltuieli.to_dict("records")

    def insert_incasari(self):
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
        records = self.get_cheltuieli_records()

        amortizari_salvate = set()
        for r in records:
            with open(r["Cale Fisier"], "rb") as f:

                di_native = datetime.strptime(r["Data"], "%Y-%m-%d")
                data_inserarii = timezone.make_aware(di_native)

                if r["Mijloc Fix"] == "Da":

                    if r["Cale Fisier"] in amortizari_salvate:
                        continue  # e salvat deja

                    dpf_native = datetime.strptime(
                        r["Data Punerii In Functiune"], "%Y-%m-%d"
                    )
                    data_punerii_in_functiune = timezone.make_aware(dpf_native)

                    incasare = CheltuialaModel(
                        suma=r["Valoare Inventar"],
                        tip_tranzactie=r["Tip Tranzactie"],
                        data_inserarii=data_inserarii,
                        fisier=File(f, name=os.path.basename(r["Cale Fisier"])),
                        nume_cheltuiala=r["Nume Cheltuiala"],
                        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA,
                        cod_de_clasificare=r["Cod Clasificare"],
                        data_punerii_in_functiune=data_punerii_in_functiune,
                        ani_amortizare=r["Ani Amortizare"],
                        scos_din_uz=r["Scos din uz"] == "Da",
                    )
                    incasare.save()
                    amortizari_salvate.add(r["Cale Fisier"])

                elif r["Obiect Inventar"] == "Da":
                    incasare = CheltuialaModel(
                        suma=r["Suma Cheltuita"],
                        tip_tranzactie=r["Tip Tranzactie"],
                        data_inserarii=data_inserarii,
                        fisier=File(f, name=os.path.basename(r["Cale Fisier"])),
                        nume_cheltuiala=r["Nume Cheltuiala"],
                        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR,
                        scos_din_uz=r["Scos din uz"] == "Da",
                    )
                    incasare.save()

                else:
                    incasare = CheltuialaModel(
                        suma=r["Suma Cheltuita"],
                        tip_tranzactie=r["Tip Tranzactie"],
                        data_inserarii=data_inserarii,
                        fisier=File(f, name=os.path.basename(r["Cale Fisier"])),
                        nume_cheltuiala=r["Nume Cheltuiala"],
                        deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL,
                    )
                    incasare.save()

    def insert_date_pfa(self):
        data = self.get_furnizor_data()

        instance = SetariModel(
            nume=data["nume"],
            localitate="RO-IS, jud. Iasi, Iasi",
            adresa=data["adresa"],
            nr_reg_com=data["nrRegCom"],
            cif=data["cif"],
            telefon=data["telefon"],
            email=data["email"],
            iban=data["iban"],
            caen_principal="6201",
        )

        instance.save()

    def insert_documente(self):

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
