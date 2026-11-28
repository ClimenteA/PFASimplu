from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.localitati import Localitati
from utils.models import UserOwnedModel
from utils.valuta import Valuta


def validate_iban_length(value):
    if len(value or "") < 24:
        raise ValidationError(_("IBAN trebuie sa aiba minim 24 de caractere."))


def validate_iban_trezoreria(value):
    """IBAN-ul trezoreriei are exact 24 de caractere si cifra de control valida."""
    iban = (value or "").replace(" ", "").upper()
    if len(iban) != 24:
        raise ValidationError(
            _("IBAN-ul trezoreriei trebuie sa aiba exact 24 de caractere.")
        )
    if not iban.startswith("RO"):
        raise ValidationError(_("IBAN-ul trezoreriei trebuie sa inceapa cu RO."))
    rearranged = iban[4:] + iban[:4]
    try:
        numeric = "".join(str(int(c, 36)) for c in rearranged)
    except ValueError:
        raise ValidationError(_("IBAN-ul trezoreriei contine caractere invalide."))
    if int(numeric) % 97 != 1:
        raise ValidationError(
            _(
                "IBAN-ul trezoreriei nu este valid (cifra de control gresita). Verifica-l in lista ANAF."
            )
        )


class SetariModel(UserOwnedModel):
    nume = models.CharField(max_length=250)
    localitate = models.CharField(max_length=250, choices=Localitati)
    adresa = models.CharField(max_length=500)
    nr_reg_com = models.CharField(max_length=50)
    cif = models.CharField(max_length=20)
    email = models.EmailField()
    telefon = models.CharField(max_length=50, blank=True, null=True)
    caen_principal = models.CharField(max_length=4)
    caen_secondare = models.JSONField(default=list, blank=True)
    scutit_cas = models.BooleanField(default=False)
    scutit_cass = models.BooleanField(default=False)
    scutit_impozit = models.BooleanField(default=False)
    actualizat_la = models.DateTimeField(default=timezone.now)

    # Codul special de TVA intracomunitar (art. 317 Cod fiscal).
    cod_tva_intracomunitar = models.CharField(max_length=20, blank=True, null=True)
    cont_iban_trezoreria = models.CharField(
        max_length=34, blank=True, null=True, validators=[validate_iban_trezoreria]
    )

    class Meta:
        verbose_name_plural = "Setari"

    def __str__(self):
        return self.nume

    def get_cif_pentru_achizitie(self, este_ue: bool) -> str:
        if este_ue and self.cod_tva_intracomunitar:
            return self.cod_tva_intracomunitar.strip().upper().removeprefix("RO")
        return (self.cif or "").strip().upper().removeprefix("RO")

    def get_iban_pentru_valuta(self, valuta: str | None = None):
        """IBAN-ul contului pentru moneda ceruta: valuta -> RON -> primul cont."""
        conturi = list(self.conturi.all())
        if valuta:
            for cont in conturi:
                if cont.valuta == valuta and cont.iban:
                    return cont.iban
        for cont in conturi:
            if cont.valuta == Valuta.RON.value and cont.iban:
                return cont.iban
        for cont in conturi:
            if cont.iban:
                return cont.iban
        return None


def are_cod_tva_intracomunitar() -> bool:
    """Codul special de TVA intracomunitar (art. 317) e completat in Setari."""
    setari = SetariModel.objects.first()
    return bool(setari and setari.cod_tva_intracomunitar)


class ContBancar(models.Model):
    """Cont bancar al PFA-ului, cu IBAN validat si unic per valuta."""

    setari = models.ForeignKey(
        SetariModel, related_name="conturi", on_delete=models.CASCADE
    )
    valuta = models.CharField(max_length=3, choices=Valuta)
    iban = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["setari", "valuta"], name="unic_cont_bancar_per_valuta"
            )
        ]

    def __str__(self):
        return f"{self.valuta}: {self.iban}"
