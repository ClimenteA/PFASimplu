# Generated by Django 5.1 on 2024-09-26 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheltuieli', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cheltuialamodel',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]