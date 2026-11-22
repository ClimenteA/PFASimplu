import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def muta_datele_din_tva(apps, schema_editor):
    """App-ul tva a fost eliminat; modelul traieste acum in documente.
    Daca tabelul vechi tva_declaratietvamodel exista (baza de date existenta),
    copiem datele in tabelul nou si stergem tabelul vechi.
    Pe o baza noua tabelul vechi nu exista, deci nu e nimic de facut."""
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        tabele = connection.introspection.table_names(cursor)
        if "tva_declaratietvamodel" in tabele:
            coloane = (
                "id, tip, anul, luna, cif_folosit, total_de_plata, "
                "randuri, status, recipisa_id, actualizat_la"
            )
            cursor.execute(
                f"INSERT INTO documente_declaratietvamodel ({coloane}) "
                f"SELECT {coloane} FROM tva_declaratietvamodel"
            )
            cursor.execute("DROP TABLE tva_declaratietvamodel")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'tva'")


class Migration(migrations.Migration):

    dependencies = [
        ("documente", "0002_alter_documentemodel_tip_document"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeclaratieTVAModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tip", models.CharField(choices=[("D301", "D301 - Decont special de TVA"), ("D390", "D390 VIES - Declaratie recapitulativa")], max_length=10)),
                ("anul", models.IntegerField()),
                ("luna", models.IntegerField()),
                ("cif_folosit", models.CharField(max_length=20)),
                ("total_de_plata", models.FloatField(default=0)),
                ("randuri", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("Calculata", "Calculata"), ("Descarcata", "Descarcata"), ("Depusa", "Depusa (recipisa)"), ("Platita", "Platita")], default="Calculata", max_length=20)),
                ("recipisa", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="declaratie_tva", to="documente.documentemodel")),
                ("actualizat_la", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "verbose_name_plural": "DeclaratiiTVA",
                "unique_together": {("tip", "anul", "luna")},
            },
        ),
        migrations.RunPython(muta_datele_din_tva, reverse_code=migrations.RunPython.noop),
    ]
