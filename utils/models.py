from django.db import models
from django.utils.translation import gettext_lazy as _
from .files import get_save_path
from .valuta import Valuta, TipTranzactie, to_ron
from .validators import validate_not_future_date
from django.utils import timezone


class CommonIncasariCheltuieliModel(models.Model):
    suma_in_ron = models.FloatField(null=True, blank=True)
    suma = models.FloatField()
    valuta = models.CharField(max_length=3, choices=Valuta, default=Valuta.RON)
    tip_tranzactie = models.CharField(
        max_length=7, choices=TipTranzactie, default=TipTranzactie.BANCAR
    )
    data_inserarii = models.DateField(
        null=True, blank=True, validators=[validate_not_future_date]
    )
    fisier = models.FileField(max_length=100_000, upload_to=get_save_path)
    actualizat_la = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.data_inserarii and self.valuta != "RON":
            self.suma_in_ron = to_ron(self.suma, self.valuta, self.data_inserarii)
        elif not self.data_inserarii and self.valuta != "RON":
            self.suma_in_ron = to_ron(self.suma, self.valuta, timezone.now().date())
        elif self.valuta == "RON":
            self.suma_in_ron = self.suma

        if hasattr(self, "deducere_in_ron"):
            self.deducere_in_ron = self.calculeaza_deducere_in_ron()

        super().save(*args, **kwargs)

    class Meta:
        abstract = True
