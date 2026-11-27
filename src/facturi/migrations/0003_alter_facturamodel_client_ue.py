from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("facturi", "0002_facturamodel_client_ue"),
    ]

    operations = [
        migrations.AlterField(
            model_name="facturamodel",
            name="client_ue",
            field=models.BooleanField(default=False, verbose_name="Client UE VIES"),
        ),
    ]
