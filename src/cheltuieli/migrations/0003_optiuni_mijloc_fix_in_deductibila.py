from django.db import migrations, models
from django.db.models import Q


def muta_checkboxurile_in_deductibila(apps, schema_editor):
    """Pastreaza tratamentul mijloacelor fixe deja introduse.

    Optiunea speciala devine o valoare a campului `deductibila`, deci
    transformam vechile checkboxuri inainte de a le sterge din baza.
    """
    CheltuialaModel = apps.get_model("cheltuieli", "CheltuialaModel")
    vechi = CheltuialaModel.objects.filter(
        Q(este_autoturism_m1=True) | Q(este_sediu_social_neexclusiv=True)
    )
    for cheltuiala in vechi.iterator():
        if cheltuiala.este_autoturism_m1:
            cheltuiala.deductibila = (
                "MIJLOC_FIX_M1_EXCEPTIE"
                if cheltuiala.exceptie_1500
                else "MIJLOC_FIX_M1"
            )
        else:
            cheltuiala.deductibila = "MIJLOC_FIX_SEDIU"
        cheltuiala.save(update_fields=["deductibila"])


class Migration(migrations.Migration):
    dependencies = [
        ("cheltuieli", "0002_cheltuialamodel_este_autoturism_m1_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cheltuialamodel",
            name="deductibila",
            field=models.CharField(
                choices=[
                    ("INTEGRAL", "Deductibila integral"),
                    ("INVENTAR", "Obiect de inventar (deductibil integral)"),
                    (
                        "MIJLOC_FIX",
                        "Mijloc fix peste 5000 RON (ded. integral cu amortizare)",
                    ),
                    (
                        "MIJLOC_FIX_SEDIU",
                        "Mijloc fix peste 5000 RON (sediu social amortizare 50%)",
                    ),
                    (
                        "MIJLOC_FIX_M1",
                        "Mijloc fix peste 5000 RON (Autoturism M1 limita 1.500 lei/luna)",
                    ),
                    (
                        "MIJLOC_FIX_M1_EXCEPTIE",
                        "Mijloc fix peste 5000 RON (Autoturism M1 cu exceptie art. 28 alin. 14, amortizare integrala)",
                    ),
                    (
                        "AUTO_50",
                        "Vehicule nefolosite exclusiv in activitate, 50% (art. 68 alin. 7 lit. k)",
                    ),
                    (
                        "BURSE",
                        "Burse private max. 5% din baza de calcul (art. 68 alin. 5 lit. a)",
                    ),
                    ("SPORT", "Sport, sali de fitness etc. max. 100 EUR pe an"),
                    ("PENSIE_III", "Pensie pilon III max. 400 EUR pe an"),
                    (
                        "PENSIE_OCUP",
                        "Pensie ocupationala max. 400 EUR pe an (din 2026)",
                    ),
                    (
                        "PEPP",
                        "Produs paneuropean de pensii (PEPP) max. 400 EUR pe an (din 1.03.2026)",
                    ),
                    ("ETF", "ETF max. 400 EUR pe an (din 1.03.2026)"),
                    ("ASIG_MED", "Asigurari medicale private max. 400 EUR pe an"),
                    ("PROTOCOL", "Mese protocol max. 2% baza de calcul"),
                    ("SALARII", "Deductibila integral salarii"),
                    (
                        "AJUTOARE",
                        "Ajutoare diverse pt. angajati max. 5% din total salarii pe an",
                    ),
                    (
                        "CONTRIB_OBLIG",
                        "Contributii obligatorii asociatii, organizatii max. 5% din brut",
                    ),
                    (
                        "COTIZATII",
                        "Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an",
                    ),
                ],
                default="INTEGRAL",
                max_length=30,
            ),
        ),
        migrations.RunPython(
            muta_checkboxurile_in_deductibila, migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="cheltuialamodel",
            name="este_autoturism_m1",
        ),
        migrations.RemoveField(
            model_name="cheltuialamodel",
            name="este_sediu_social_neexclusiv",
        ),
        migrations.RemoveField(
            model_name="cheltuialamodel",
            name="exceptie_1500",
        ),
    ]
