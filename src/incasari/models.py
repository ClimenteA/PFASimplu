from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.decimale import D, rotund2
from utils.models import CommonIncasariCheltuieliModel


class SursaVenit(models.TextChoices):
    ACTIVITATE_PRINCIPALA = "ACTIVITATE", _("Venit din activitati independente")
    ALTE_SURSE = "ALTE", _("Venit din alte surse")
    INCHIRIERI = "INCHIRIERI", _("Venit din cedarea folosintei bunurilor")
    CASTIG_INVESTITII = "INVESTITII", _("Venit si/sau castig din investitii")
    DREPTURI_PROP_INTELECTUALA = (
        "PROPRIETATE_INTELLECTUALA",
        _("Venit din drepturi de proprietate intelectuala"),
    )
    AGRICULTURA = (
        "AGRICULTURA",
        _("Venit din activitati agricole, silvicultura si piscicultura"),
    )
    DIVIDENTE_VENIT_DISTRUBUIT = (
        "DIVIDENTE",
        _(
            "Venit distribuit din asociere cu persoane juridice, contribuabili potrivit "
            "prevederilor titlului II, titlului III sau Legii nr.170/2016"
        ),
    )


class IncasariModel(CommonIncasariCheltuieliModel):
    sursa_venit = models.CharField(
        max_length=30, choices=SursaVenit, default=SursaVenit.ACTIVITATE_PRINCIPALA
    )
    # Data la care banii au intrat in cont. NULL inseamna "in asteptare".
    # `data_inserarii` ramane data operatiunii documentului.
    data_incasarii = models.DateField(null=True, blank=True)
    factura = models.OneToOneField(
        "facturi.FacturaModel",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incasare",
    )

    @property
    def este_incasata(self):
        return self.data_incasarii is not None

    @staticmethod
    def get_total_incasari_pe_luni(year: int):
        sume = [D(0) for _ in range(12)]
        for incasare in IncasariModel.objects.filter(
            data_incasarii__isnull=False, data_incasarii__year=year
        ):
            sume[incasare.data_incasarii.month - 1] += D(incasare.suma_in_ron)
        return sume

    @staticmethod
    def get_total_neincasate(year: int):
        total = D(0)
        for incasare in IncasariModel.objects.filter(
            data_incasarii__isnull=True, actualizat_la__year=year
        ):
            total += D(incasare.suma_in_ron)
        return rotund2(total)

    @staticmethod
    def get_total_incasari(year: int):
        total = D(0)
        for incasare in IncasariModel.objects.filter(
            data_incasarii__isnull=False, data_incasarii__year=year
        ):
            total += D(incasare.suma_in_ron)
        return rotund2(total)

    @staticmethod
    def get_total_incasari_alte_surse(year: int):
        """Total incasari din categorii diferite de activitatea independenta.

        Pentru acestea CASS se calculeaza pe trepte de 6/12/24 salarii minime
        (art. 170 alin. 2-3 din Codul fiscal), nu liniar ca la PFA.
        """
        total = D(0)
        for incasare in IncasariModel.objects.filter(
            data_incasarii__isnull=False, data_incasarii__year=year
        ).exclude(sursa_venit=SursaVenit.ACTIVITATE_PRINCIPALA.value):
            total += D(incasare.suma_in_ron)
        return rotund2(total)

    class Meta:
        app_label = "incasari"
        verbose_name_plural = "Incasari"

    def __str__(self):
        return f"{self.sursa_venit} {self.suma_in_ron}RON {self.actualizat_la}"
