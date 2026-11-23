from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from utils.localitati import Localitati
from utils.models import UserOwnedModel, UserScopedManager
from utils.valuta import Valuta


def validate_iban_length(value):
    if len(value) < 24:
        raise ValidationError(_("IBAN trebuie sa aiba minim 24 de caractere."))


def validate_iban_trezoreria(value):
    """IBAN-ul trezoreriei are exact 24 de caractere si cifra de control valida
    (contine litere in BBAN, ex. RO41TREZ40620A100101XTVA)."""
    iban = (value or "").replace(" ", "").upper()
    if len(iban) != 24:
        raise ValidationError(_("IBAN-ul trezoreriei trebuie sa aiba exact 24 de caractere."))
    if not iban.startswith("RO"):
        raise ValidationError(_("IBAN-ul trezoreriei trebuie sa inceapa cu RO."))
    rearranged = iban[4:] + iban[:4]
    try:
        numeric = "".join(str(int(c, 36)) for c in rearranged)
    except ValueError:
        raise ValidationError(_("IBAN-ul trezoreriei contine caractere invalide."))
    if int(numeric) % 97 != 1:
        raise ValidationError(_("IBAN-ul trezoreriei nu este valid (cifra de control gresita). Verifica-l in lista ANAF."))


class SetariModel(UserOwnedModel):
    nume = models.CharField(max_length=250)
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
    scutit_cas = models.BooleanField(blank=True, null=True, default=False)
    scutit_cass = models.BooleanField(blank=True, null=True, default=False)
    scutit_impozit = models.BooleanField(blank=True, null=True, default=False)
    actualizat_la = models.DateTimeField(default=timezone.now)

    conturi_iban = models.JSONField(default=list, blank=True)

    # Codul special de TVA intracomunitar (art. 317 Cod fiscal), diferit de CIF-ul normal.
    # Se foloseste pentru achizitiile de servicii din UE si in declaratiile D301/D390.
    cod_tva_intracomunitar = models.CharField(max_length=20, blank=True, null=True)

    # IBAN-ul trezoreriei pentru plata TVA din D301 (cod bugetar 20A100101).
    # Utilizatorul il ia din lista ANAF pentru judetul/localitatea lui (link in Setari).
    cont_iban_trezoreria = models.CharField(
        max_length=34, blank=True, null=True, validators=[validate_iban_trezoreria]
    )

    objects = UserScopedManager()

    class Meta:
        verbose_name_plural = "Setari"

    def __str__(self):
        return self.nume

    def get_cif_pentru_achizitie(self, este_ue: bool) -> str:
        """CIF-ul folosit in D301/D390 si la plata TVA:
        - achizitii din UE: codul special de TVA intracomunitar (art. 317), daca exista;
        - achizitii non-UE: codul normal de PFA (CIF)."""
        if este_ue and self.cod_tva_intracomunitar:
            return self.cod_tva_intracomunitar.strip().upper().removeprefix("RO")
        return (self.cif or "").strip().upper().removeprefix("RO")

    def get_iban_pentru_valuta(self, valuta: str | None = None):
        """Returneaza IBAN-ul contului pentru moneda ceruta.
        Daca nu exista un cont in moneda ceruta se foloseste contul de RON,
        iar daca nici acesta nu exista, primul cont disponibil."""

        conturi = self.conturi_iban or []

        if valuta:
            for cont in conturi:
                if cont.get("valuta") == valuta and cont.get("iban"):
                    return cont["iban"]

        for cont in conturi:
            if cont.get("valuta") == Valuta.RON.value and cont.get("iban"):
                return cont["iban"]

        for cont in conturi:
            if cont.get("iban"):
                return cont["iban"]

        return self.iban
