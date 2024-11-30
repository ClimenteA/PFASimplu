import os
import shutil
import pandas as pd
from documente.models import DocumenteModel
from incasari.models import IncasariModel
from cheltuieli.models import CheltuialaModel
from setari.models import SetariModel
from facturi.models import FacturaModel
from django.utils import timezone
from datetime import datetime
from core.settings import get_media_path



class DataImportV2:

    def insert_date_pfa(self):

        df = pd.read_csv(os.path.join("stocare", "Setari.csv"))

        data = df.to_records("dict")[0]
        df = df.astype(object).where(df.notna(), None)
        data = df.to_dict('records')[0]

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

        df = pd.read_csv(os.path.join("stocare", "Incasari.csv"))
        df = df.astype(object).where(df.notna(), None)
        records = df.to_dict('records')

        media_path = get_media_path()

        for record in records:
            filepath = os.path.join("stocare", record["fisier"])
            shutil.copy2(filepath, os.path.join(media_path, record["fisier"]))

            incasare = IncasariModel(
                sursa_venit=record['sursa_venit'],
                suma_in_ron=record['suma_in_ron'],
                suma=record['suma'],
                valuta=record['valuta'],
                tip_tranzactie=record['tip_tranzactie'],
                data_inserarii=record['data_inserarii'],
                fisier=record['fisier'],
            )
            incasare.save()

    def insert_cheltuieli(self):

        df = pd.read_csv(os.path.join("stocare", "Cheltuiala.csv"))
        df = df.astype(object).where(df.notna(), None)
        records = df.to_dict('records')
        media_path = get_media_path()

        for record in records:
            filepath = os.path.join("stocare", record["fisier"])
            shutil.copy2(filepath, os.path.join(media_path, record["fisier"]))

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
    
        df = pd.read_csv(os.path.join("stocare", "Documente.csv"))
        df = df.astype(object).where(df.notna(), None)
        records = df.to_dict('records')
        media_path = get_media_path()

        for record in records:
            filepath = os.path.join("stocare", record["fisier"])
            shutil.copy2(filepath, os.path.join(media_path, record["fisier"]))

            instance = DocumenteModel(
                tip_document=record["tip_document"],
                document_pentru_anul=record["document_pentru_anul"],
                mentiuni=record["mentiuni"],
                fisier=record["fisier"],
                parse_tip_document=False,
            )
            instance.save()

    def insert_facturi(self):

        df = pd.read_csv(os.path.join("stocare", "Factura.csv"))
        df = df.astype(object).where(df.notna(), None)
        records = df.to_dict('records')
        media_path = get_media_path()

        for record in records:
            filepath_fisier_factura_pdf = os.path.join("stocare", record["filepath_fisier_factura_pdf"])
            # TODO
            if filepath_fisier_efactura_xml:
                filepath_fisier_efactura_xml = os.path.join("stocare", record["filepath_fisier_efactura_xml"])
                shutil.copy2(filepath_fisier_efactura_xml, os.path.join(media_path, record["filepath_fisier_efactura_xml"]))

            if filepath_fisier_efactura_xml:
                shutil.copy2(filepath_fisier_efactura_xml, os.path.join(media_path, record["filepath_fisier_efactura_xml"]))


            instance = FacturaModel(
                # serie = models.CharField(max_length=20)
                # numar = models.IntegerField()
                # data_emitere = models.DateTimeField(default=timezone.now)
                # data_scadenta = models.DateTimeField(default=one_month_from_now)
                # tip_factura = models.CharField(
                #     max_length=300,
                #     choices=TipFactura,
                #     default=TipFactura.E_FACTURA,
                # )
                # # Client
                # nume = models.CharField(max_length=200)
                # cif = models.CharField(max_length=50)
                # nr_reg_com = models.CharField(max_length=50, null=True, blank=True)
                # localitate = models.CharField(
                #     max_length=250,
                #     choices=Localitati,
                #     null=True,
                #     blank=True,
                #     default=Localitati.LOCALITATE_GENERIC,
                # )
                # adresa = models.CharField(max_length=1000)
                # email = models.EmailField(max_length=250, null=True, blank=True)
                # telefon = models.CharField(max_length=250, null=True, blank=True)
                # # Plata
                # tip_tranzactie = models.CharField(
                #     max_length=250, choices=ModalitatePlata, default=ModalitatePlata.BANCAR
                # )
                # total_de_plata = models.FloatField()
                # valuta = models.CharField(max_length=3, choices=Valuta, default=Valuta.RON)
                # # Produse sau servicii
                # # id, numar_unitati, total_de_plata, nume_produs_sau_serviciu, cod_unitate, pret_pe_unitate, subtotal
                # produse_sau_servicii = models.JSONField(default=list)
                # nota = models.TextField(max_length=5000, null=True, blank=True)
                # data_inserarii = models.DateTimeField(default=timezone.now, null=True, blank=True)

                # # Fisiere
                # fisier_efactura_xml = models.FileField(
                #     max_length=100_000, upload_to=get_save_path, null=True, blank=True
                # )
                # fisier_factura_pdf = models.FileField(
                #     max_length=100_000, upload_to=get_save_path, null=True, blank=True
                # )
            )
            instance.save()

