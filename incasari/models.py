import datetime
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from utils.models import CommonIncasariCheltuieliModel
from django.db.models.functions import TruncMonth


class SursaVenit(models.TextChoices):
    ACTIVITATE_PRINCIPALA = "Venit din activitati independente", _(
        "Venit din activitati independente"
    )
    ALTE_SURSE = "Venit din alte surse", _("Venit din alte surse")
    INCHIRIERI = "Venit din cedarea folosintei bunurilor", _(
        "Venit din cedarea folosintei bunurilor"
    )
    CASTIG_INVESTITII = "Venit si/sau castig din investitii", _(
        "Venit si/sau castig din investitii"
    )
    DREPTURI_PROP_INTELECTUALA = "Venit din drepturi de proprietate intelectuala", _(
        "Venit din drepturi de proprietate intelectuala"
    )
    AGRICULTURA = "Venit din activitati agricole, silvicultura si piscicultura", _(
        "Venit din activitati agricole, silvicultura si piscicultura"
    )
    DIVIDENTE_VENIT_DISTRUBUIT = (
        "Venit distribuit din asociere cu persoane juridice, contribuabili potrivit prevederilor titlului II, titlului III sau Legii nr.170/2016",
        _(
            "Venit distribuit din asociere cu persoane juridice, contribuabili potrivit prevederilor titlului II, titlului III sau Legii nr.170/2016"
        ),
    )


class IncasariModel(CommonIncasariCheltuieliModel):
    sursa_venit = models.CharField(
        max_length=300, choices=SursaVenit, default=SursaVenit.ACTIVITATE_PRINCIPALA
    )

    @staticmethod
    def get_total_incasari_pe_luni(year: int):
        incasari_pe_luni = IncasariModel.objects.filter(
            data_inserarii__isnull=False,
            data_inserarii__year=year
        ).annotate(
            month=TruncMonth('data_inserarii')
        ).values('month').annotate(
            tni=Sum('suma_in_ron')
        ).order_by('month')

        data_dict = {entry['month']: entry['tni'] for entry in incasari_pe_luni}

        sume_incasari_pe_luni = []
        for month in range(1, 13):
            month_date = datetime.date(year, month, 1)
            val = data_dict.get(month_date, 0)
            sume_incasari_pe_luni.append(val)

        return sume_incasari_pe_luni

    @staticmethod
    def get_total_neincasate(year: int):
        total_neincasate = IncasariModel.objects.filter(
            data_inserarii__isnull=True,
            actualizat_la__year=year
        ).aggregate(tni=Sum("suma_in_ron"))
        total_neincasate = total_neincasate["tni"] or 0
        return total_neincasate

    @staticmethod
    def get_total_incasari(year: int):
        total_incasari_result = IncasariModel.objects.filter(
            data_inserarii__isnull=False,
            data_inserarii__year=year
        ).aggregate(totali=Sum('suma_in_ron'))

        if total_incasari_result["totali"] is None:
            total_incasari = 0
        else:
            total_incasari = total_incasari_result["totali"]

        return total_incasari


    class Meta:
        app_label = "incasari"
        verbose_name_plural = "Incasari"

    def __str__(self):
        return f"{self.sursa_venit} {self.suma_in_ron}RON {self.actualizat_la}"
