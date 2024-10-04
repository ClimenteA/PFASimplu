# Generated by Django 5.1 on 2024-10-04 13:45

import django.utils.timezone
import utils.files
import utils.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CheltuialaModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suma_in_ron', models.FloatField(blank=True, null=True)),
                ('suma', models.FloatField()),
                ('valuta', models.CharField(choices=[('RON', 'RON - Romania'), ('EUR', 'EUR - European Union Zone'), ('USD', 'USD - USA'), ('GBP', 'GBP - UK'), ('CHF', 'CHF - Switzerland'), ('CAD', 'CAD - Canada'), ('AED', 'AED - UAE'), ('AUD', 'AUD - Australia'), ('BGN', 'BGN - Bulgaria'), ('BRL', 'BRL - Brazil'), ('CNY', 'CNY - China'), ('CZK', 'CZK - Czech Republic'), ('DKK', 'DKK - Denmark'), ('EGP', 'EGP - Egypt'), ('HUF', 'HUF - Hungary'), ('INR', 'INR - India'), ('JPY', 'JPY - Japan'), ('KRW', 'KRW - South Korea'), ('MDL', 'MDL - Moldova'), ('MXN', 'MXN - Mexico'), ('NOK', 'NOK - Norway'), ('NZD', 'NZD - New Zealand'), ('PLN', 'PLN - Poland'), ('RSD', 'RSD - Serbia'), ('RUB', 'RUB - Russia'), ('SEK', 'SEK - Sweden'), ('THB', 'THB - Thailand'), ('TRY', 'TRY - Turkey'), ('UAH', 'UAH - Ukraine'), ('XAU', 'XAU - Gold'), ('XDR', 'XDR - IMF Special Drawing Rights'), ('ZAR', 'ZAR - South Africa')], default='RON', max_length=3)),
                ('tip_tranzactie', models.CharField(choices=[('BANCAR', '💳 BANCAR'), ('NUMERAR', '💵 NUMERAR')], default='BANCAR', max_length=7)),
                ('data_inserarii', models.DateField(blank=True, null=True, validators=[utils.validators.validate_not_future_date])),
                ('fisier', models.FileField(max_length=100000, upload_to=utils.files.get_save_path)),
                ('actualizat_la', models.DateTimeField(default=django.utils.timezone.now)),
                ('nume_cheltuiala', models.CharField(max_length=10000)),
                ('deductibila', models.CharField(choices=[('Deductibila integral', 'Deductibila integral'), ('Obiect de inventar (deductibil integral)', 'Obiect de inventar (deductibil integral)'), ('Mijloc fix peste 2500 RON (ded. integral cu amortizare)', 'Mijloc fix peste 2500 RON (ded. integral cu amortizare)'), ('Auto, chirii, utilitati 50% din valoarea lor', 'Auto, chirii, utilitati 50% din valoarea lor'), ('Sport, sali de fitness etc. max. 100 EUR pe an', 'Sport, sali de fitness etc. max. 100 EUR pe an'), ('Pensie pilon III max. 400 EUR pe an', 'Pensie pilon III max. 400 EUR pe an'), ('Asigurari medicale private max. 400 EUR pe an', 'Asigurari medicale private max. 400 EUR pe an'), ('Mese protocol max. 2% baza de calcul', 'Mese protocol max. 2% baza de calcul'), ('Deductibila integral salarii', 'Deductibila integral salarii'), ('Ajutoare diverse pt. angajati max. 5% din total salarii pe an', 'Ajutoare diverse pt. angajati max. 5% din total salarii pe an'), ('Contributii obligatorii asociatii, organizatii max. 5% din brut', 'Contributii obligatorii asociatii, organizatii max. 5% din brut'), ('Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an', 'Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an')], default='Deductibila integral', max_length=300)),
                ('deducere_in_ron', models.FloatField(blank=True, null=True)),
                ('obiect_de_inventar', models.BooleanField(blank=True, default=False, null=True)),
                ('mijloc_fix', models.BooleanField(blank=True, default=False, null=True)),
                ('cod_de_clasificare', models.CharField(blank=True, max_length=100, null=True)),
                ('grupa', models.CharField(blank=True, max_length=100, null=True)),
                ('data_punerii_in_functiune', models.DateField(blank=True, null=True)),
                ('data_amortizarii_complete', models.DateField(blank=True, null=True)),
                ('data_inceperii_amortizarii', models.DateField(blank=True, null=True)),
                ('durata_normala_de_functionare', models.CharField(blank=True, max_length=50, null=True)),
                ('anul_darii_in_folosinta', models.IntegerField(blank=True, null=True)),
                ('luna_darii_in_folosinta', models.IntegerField(blank=True, null=True)),
                ('anul_amortizarii_complete', models.IntegerField(blank=True, null=True)),
                ('luna_amortizarii_complete', models.IntegerField(blank=True, null=True)),
                ('ani_amortizare', models.IntegerField(blank=True, null=True)),
                ('amortizare_lunara', models.FloatField(blank=True, null=True)),
                ('cota_de_amortizare', models.FloatField(blank=True, null=True)),
                ('scos_din_uz', models.BooleanField(blank=True, default=False, null=True)),
                ('modalitate_iesire_din_uz', models.CharField(blank=True, choices=[('Casat', 'Casat'), ('Vandut', 'Vandut'), ('Donat', 'Donat'), ('Pierdut', 'Pierdut')], max_length=300, null=True)),
                ('data_iesirii_din_uz', models.DateField(blank=True, null=True, validators=[utils.validators.validate_not_future_date])),
                ('document_justificativ_iesire_din_uz', models.FileField(blank=True, null=True, upload_to=utils.files.get_save_path)),
            ],
            options={
                'verbose_name_plural': 'Cheltuieli',
            },
        ),
    ]
