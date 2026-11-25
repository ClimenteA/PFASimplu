from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.files import get_save_path
from utils.models import CommonIncasariCheltuieliModel
from utils.tari import TARI_CHOICES
from utils.validators import validate_not_future_date


class TipAchizitie(models.TextChoices):
    ROMANIA = "Romania", _("Romania (furnizor roman)")
    SERVICII_UE = "Servicii UE", _("Servicii din UE (taxare inversa)")
    SERVICII_NON_UE = "Servicii non-UE", _("Servicii din afara UE (taxare inversa)")


class Deductibilitate(models.TextChoices):
    DEDUCTIBILA_INTEGRAL = "INTEGRAL", _("Deductibila integral")
    DEDUCTIBILA_INTEGRAL_INVENTAR = (
        "INVENTAR",
        _("Obiect de inventar (deductibil integral)"),
    )
    # Eticheta afiseaza pragul actual (5000 RON, OUG 8/2026); baza fiind noua,
    # valoarea stocata poate fi si ea un cod scurt, fara compatibilitate veche.
    DEDUCTIBILA_INTEGRAL_AMORTIZATA = (
        "MIJLOC_FIX",
        _("Mijloc fix peste 5000 RON (ded. integral cu amortizare)"),
    )
    DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI = (
        "AUTO_50",
        _("Vehicule nefolosite exclusiv in activitate, 50% (art. 68 alin. 7 lit. k)"),
    )
    DEDUCTIBILA_PARTIAL_SPORT_2024 = (
        "SPORT",
        _("Sport, sali de fitness etc. max. 100 EUR pe an"),
    )
    DEDUCTIBILA_PARTIAL_PENSIE_PILON_3 = (
        "PENSIE_III",
        _("Pensie pilon III max. 400 EUR pe an"),
    )
    DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT = (
        "ASIG_MED",
        _("Asigurari medicale private max. 400 EUR pe an"),
    )
    DEDUCTIBILA_PARTIAL_PROTOCOL = "PROTOCOL", _("Mese protocol max. 2% baza de calcul")
    DEDUCTIBILA_INTEGRAL_SALARII = "SALARII", _("Deductibila integral salarii")
    DEDUCTIBILA_PARTIAL_SOCIALE = (
        "AJUTOARE",
        _("Ajutoare diverse pt. angajati max. 5% din total salarii pe an"),
    )
    DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG = (
        "CONTRIB_OBLIG",
        _("Contributii obligatorii asociatii, organizatii max. 5% din brut"),
    )
    DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG = (
        "COTIZATII",
        _("Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an"),
    )


class ModalitateIesireDinUz(models.TextChoices):
    CASAT = "CASAT", _("Casat")
    VANDUT = "VANDUT", _("Vandut")
    DONAT = "DONAT", _("Donat")
    PIERDUT = "PIERDUT", _("Pierdut")


# Valori care in versiunea veche erau coloane in baza. Le acceptam la crearea
# obiectelor (compatibilitate cu codul si testele existente), dar nu mai sunt
# stocate: intotdeauna se recalculeaza din faptele introduse de utilizator.
_DERIVED = frozenset(
    {
        "suma_in_ron",
        "deducere_in_ron",
        "obiect_de_inventar",
        "mijloc_fix",
        "grupa",
        "durata_normala_de_functionare",
        "data_amortizarii_complete",
        "data_inceperii_amortizarii",
        "anul_darii_in_folosinta",
        "luna_darii_in_folosinta",
        "anul_amortizarii_complete",
        "luna_amortizarii_complete",
        "amortizare_lunara",
        "cota_de_amortizare",
        "scos_din_uz",
        "tip_achizitie",
        "curs_bnr_aplicat",
        "baza_in_lei",
        "tva_autolichidata",
    }
)


class CheltuialaModel(CommonIncasariCheltuieliModel):
    """O cheltuiala: doar faptele introduse de utilizator.

    Toate sumele calculate si datele amortizarii sunt expuse ca proprietati
    din `cheltuieli/calcul.py`, deci nu pot diverga de datele de intrare.
    """

    nume_cheltuiala = models.CharField(max_length=300)
    deductibila = models.CharField(
        max_length=30,
        choices=Deductibilitate,
        default=Deductibilitate.DEDUCTIBILA_INTEGRAL,
    )
    cod_de_clasificare = models.CharField(max_length=100, null=True, blank=True)
    # Doar suprascrierea optionala a duratei din catalog; altfel se deriva.
    ani_amortizare = models.IntegerField(null=True, blank=True)
    data_punerii_in_functiune = models.DateField(null=True, blank=True)

    # Iesirea din uz a unui obiect de inventar / mijloc fix
    modalitate_iesire_din_uz = models.CharField(
        max_length=30,
        choices=ModalitateIesireDinUz,
        null=True,
        blank=True,
    )
    data_iesirii_din_uz = models.DateField(
        null=True, blank=True, validators=[validate_not_future_date]
    )
    document_justificativ_iesire_din_uz = models.FileField(
        null=True, blank=True, upload_to=get_save_path
    )

    # Achizitii de servicii din UE/non-UE cu taxare inversa (art. 307 alin. (2)).
    # Originea (RO / UE / non-UE) se deduce din tara furnizorului.
    furnizor_denumire = models.CharField(max_length=500, null=True, blank=True)
    furnizor_cod_fiscal = models.CharField(max_length=100, null=True, blank=True)
    furnizor_tara = models.CharField(
        max_length=2, null=True, blank=True, choices=TARI_CHOICES
    )
    numar_factura = models.CharField(max_length=200, null=True, blank=True)
    data_facturii = models.DateField(
        null=True, blank=True, validators=[validate_not_future_date]
    )

    class Meta:
        app_label = "cheltuieli"
        verbose_name_plural = "Cheltuieli"

    def __init__(self, *args, **kwargs):
        for camp in _DERIVED:
            kwargs.pop(camp, None)
        super().__init__(*args, **kwargs)

    # --- campuri derivate ----------------------------------------------------
    # Importul este local pentru a evita un ciclu: calcul.py foloseste modelul,
    # iar modelul expune functiile din calcul.py.

    @property
    def deducere_in_ron(self):
        from .calcul import deducere_in_ron

        return deducere_in_ron(self)

    @property
    def obiect_de_inventar(self):
        from .calcul import obiect_de_inventar

        return obiect_de_inventar(self)

    @property
    def mijloc_fix(self):
        from .calcul import mijloc_fix

        return mijloc_fix(self)

    @property
    def grupa(self):
        from .calcul import grupa

        return grupa(self)

    @property
    def durata_normala_de_functionare(self):
        from .calcul import durata_normala_de_functionare

        return durata_normala_de_functionare(self)

    @property
    def data_inceperii_amortizarii(self):
        from .calcul import data_inceperii_amortizarii

        return data_inceperii_amortizarii(self)

    @property
    def data_amortizarii_complete(self):
        from .calcul import data_amortizarii_complete

        return data_amortizarii_complete(self)

    @property
    def amortizare_lunara(self):
        from .calcul import amortizare_lunara

        return amortizare_lunara(self)

    @property
    def cota_de_amortizare(self):
        from .calcul import cota_de_amortizare

        return cota_de_amortizare(self)

    @property
    def anul_darii_in_folosinta(self):
        from .calcul import anul_darii_in_folosinta

        return anul_darii_in_folosinta(self)

    @property
    def luna_darii_in_folosinta(self):
        from .calcul import luna_darii_in_folosinta

        return luna_darii_in_folosinta(self)

    @property
    def anul_amortizarii_complete(self):
        from .calcul import anul_amortizarii_complete

        return anul_amortizarii_complete(self)

    @property
    def luna_amortizarii_complete(self):
        from .calcul import luna_amortizarii_complete

        return luna_amortizarii_complete(self)

    @property
    def scos_din_uz(self):
        from .calcul import scos_din_uz

        return scos_din_uz(self)

    @property
    def tip_achizitie(self):
        from .calcul import tip_achizitie

        return tip_achizitie(self)

    @property
    def este_taxare_inversa(self):
        from .calcul import este_taxare_inversa

        return este_taxare_inversa(self)

    @property
    def este_ue(self):
        from .calcul import este_ue

        return este_ue(self)

    @property
    def curs_bnr_aplicat(self):
        from .calcul import curs_bnr_aplicat

        return curs_bnr_aplicat(self)

    @property
    def baza_in_lei(self):
        from .calcul import baza_in_lei

        return baza_in_lei(self)

    @property
    def tva_autolichidata(self):
        from .calcul import tva_autolichidata

        return tva_autolichidata(self)

    # --- validare / salvare --------------------------------------------------

    def clean(self):
        from .calcul import valideaza

        valideaza(self)

    def save(self, *args, **kwargs):
        # Validarea ramane si la save() pentru obiectele create direct prin ORM.
        self.clean()
        super().save(*args, **kwargs)

    # --- API folosit de dashboard/registre ----------------------------------

    def luni_amortizare_active_in_an(self, year: int):
        from .calcul import luni_amortizare_active_in_an

        return luni_amortizare_active_in_an(self, year)

    def luni_amortizare_in_an(self, year: int):
        return len(self.luni_amortizare_active_in_an(year))

    @staticmethod
    def get_total_cheltuieli(year: int):
        from .calcul import get_total_cheltuieli

        return get_total_cheltuieli(year)

    @staticmethod
    def get_total_cheltuieli_pe_luni(year: int):
        from .calcul import get_total_cheltuieli_pe_luni

        return get_total_cheltuieli_pe_luni(year)

    def __str__(self):
        return f"{self.deductibila} {self.deducere_in_ron}RON {self.actualizat_la.isoformat()}"
