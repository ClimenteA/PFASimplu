# Generated by Django 5.1 on 2024-10-07 12:37

import documente.models
import utils.files
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DocumenteModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tip_document', models.CharField(choices=[('Document util', 'Document util'), ('Dovada plata taxe si impozite', 'Dovada plata taxe si impozite'), ('Declaratie unica 212', 'Declaratie unica 212'), ('Declaratie unica 212 dovada incarcare', 'Declaratie unica 212 dovada incarcare'), ('Declaratie inregistrare PFA in scop TVA 097', 'Declaratie inregistrare PFA in scop TVA 097'), ('Declaratie inregistrare PFA in scop TVA 097 dovada incarcare', 'Declaratie inregistrare PFA in scop TVA 097 dovada incarcare'), ('Declaratie decont TVA 300', 'Declaratie decont TVA 300'), ('Declaratie decont TVA 300 dovada incarcare', 'Declaratie decont TVA 300 dovada incarcare'), ('Declaratie activitate financiara 392A', 'Declaratie activitate financiara 392A'), ('Declaratie activitate financiara 392A dovada incarcare', 'Declaratie activitate financiara 392A dovada incarcare'), ('Declaratie activitate financiara 392B', 'Declaratie activitate financiara 392B'), ('Declaratie activitate financiara 392B dovada incarcare', 'Declaratie activitate financiara 392B dovada incarcare'), ('Declaratie obligatii de plata pentru salariati 112', 'Declaratie obligatii de plata pentru salariati 112'), ('Declaratie obligatii de plata pentru salariati 112 dovada incarcare', 'Declaratie obligatii de plata pentru salariati 112  dovada incarcare')], default='Declaratie unica 212', max_length=300)),
                ('document_pentru_anul', models.IntegerField(blank=True, null=True, validators=[documente.models.validate_year])),
                ('mentiuni', models.TextField(blank=True, max_length=50000, null=True)),
                ('fisier', models.FileField(max_length=100000, upload_to=utils.files.get_save_path)),
                ('actualizat_la', models.DateTimeField(auto_now_add=True)),
                ('parse_tip_document', models.BooleanField(blank=True, default=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Documente',
            },
        ),
    ]
