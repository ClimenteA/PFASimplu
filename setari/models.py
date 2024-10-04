from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from utils.localitati import Localitati


def validate_iban_length(value):
    if len(value) < 24:
        raise ValidationError(_("IBAN trebuie sa aiba minim 24 de caractere."))


class SetariModel(models.Model):
    nume = models.CharField(max_length=50)
    localitate = models.CharField(max_length=250, choices=Localitati)
    adresa = models.CharField(max_length=500)
    nr_reg_com = models.CharField(max_length=50)
    cif = models.CharField(max_length=20)
    email = models.EmailField()
    telefon = models.CharField(max_length=50, blank=True, null=True)
    iban = models.CharField(
        max_length=50, blank=True, null=True, validators=[validate_iban_length]
    )
    caen_principal = models.CharField(max_length=4)
    caen_secondar_1 = models.CharField(max_length=4, blank=True, null=True)
    caen_secondar_2 = models.CharField(max_length=4, blank=True, null=True)
    caen_secondar_3 = models.CharField(max_length=4, blank=True, null=True)
    caen_secondar_4 = models.CharField(max_length=4, blank=True, null=True)
    caen_secondar_5 = models.CharField(max_length=4, blank=True, null=True)
    actualizat_la = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Setari"

    def __str__(self):
        return self.nume
