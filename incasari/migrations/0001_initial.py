# Generated by Django 5.1 on 2024-09-27 10:27

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
            name='IncasariModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suma_in_ron', models.FloatField(blank=True, null=True)),
                ('suma', models.FloatField()),
                ('valuta', models.CharField(choices=[('RON', '🇷🇴 RON - Romania'), ('EUR', '🇪🇺 EUR - European Union Zone'), ('USD', '🇺🇸 USD - USA'), ('GBP', '🇬🇧 GBP - UK'), ('CHF', '🇨🇭 CHF - Switzerland'), ('CAD', '🇨🇦 CAD - Canada'), ('AED', '🇦🇪 AED - UAE'), ('AUD', '🇦🇺 AUD - Australia'), ('BGN', '🇧🇬 BGN - Bulgaria'), ('BRL', '🇧🇷 BRL - Brazil'), ('CNY', '🇨🇳 CNY - China'), ('CZK', '🇨🇿 CZK - Czech Republic'), ('DKK', '🇩🇰 DKK - Denmark'), ('EGP', '🇪🇬 EGP - Egypt'), ('HUF', '🇭🇺 HUF - Hungary'), ('INR', '🇮🇳 INR - India'), ('JPY', '🇯🇵 JPY - Japan'), ('KRW', '🇰🇷 KRW - South Korea'), ('MDL', '🇲🇩 MDL - Moldova'), ('MXN', '🇲🇽 MXN - Mexico'), ('NOK', '🇳🇴 NOK - Norway'), ('NZD', '🇳🇿 NZD - New Zealand'), ('PLN', '🇵🇱 PLN - Poland'), ('RSD', '🇷🇸 RSD - Serbia'), ('RUB', '🇷🇺 RUB - Russia'), ('SEK', '🇸🇪 SEK - Sweden'), ('THB', '🇹🇭 THB - Thailand'), ('TRY', '🇹🇷 TRY - Turkey'), ('UAH', '🇺🇦 UAH - Ukraine'), ('XAU', '🏅 XAU - Gold'), ('XDR', '🌐 XDR - IMF Special Drawing Rights'), ('ZAR', '🇿🇦 ZAR - South Africa')], default='RON', max_length=3)),
                ('tip_tranzactie', models.CharField(choices=[('BANCAR', '💳 BANCAR'), ('NUMERAR', '💵 NUMERAR')], default='BANCAR', max_length=7)),
                ('data_inserarii', models.DateField(blank=True, null=True, validators=[utils.validators.validate_not_future_date])),
                ('fisier', models.FileField(max_length=100000, upload_to=utils.files.get_save_path)),
                ('actualizat_la', models.DateTimeField(default=django.utils.timezone.now)),
                ('sursa_venit', models.CharField(choices=[('Venit din activitati independente', 'Venit din activitati independente'), ('Venit din alte surse', 'Venit din alte surse'), ('Venit din cedarea folosintei bunurilor', 'Venit din cedarea folosintei bunurilor'), ('Venit si/sau castig din investitii', 'Venit si/sau castig din investitii'), ('Venit din drepturi de proprietate intelectuala', 'Venit din drepturi de proprietate intelectuala'), ('Venit din activitati agricole, silvicultura si piscicultura', 'Venit din activitati agricole, silvicultura si piscicultura'), ('Venit distribuit din asociere cu persoane juridice, contribuabili potrivit prevederilor titlului II, titlului III sau Legii nr.170/2016', 'Venit distribuit din asociere cu persoane juridice, contribuabili potrivit prevederilor titlului II, titlului III sau Legii nr.170/2016')], default='Venit din activitati independente', max_length=300)),
            ],
            options={
                'verbose_name_plural': 'Incasari',
            },
        ),
    ]
