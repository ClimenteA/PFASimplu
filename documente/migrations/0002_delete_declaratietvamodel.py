# Generated manually: tabelul de declaratii TVA (D301/D390) a fost scos din UI;
# declaratiile se genereaza la cerere din pagina Cheltuieli (filtru pe luna + Descarca).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documente', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DeclaratieTVAModel',
        ),
    ]
