import datetime
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from utils.models import CommonIncasariCheltuieliModel
from utils.files import get_save_path
from dateutil.relativedelta import relativedelta
from utils.valuta import to_ron
from django.core.exceptions import ValidationError
from utils.calcule import get_venit_net, get_venit_brut
from django.utils import timezone
from utils.validators import validate_not_future_date
from django.db.models.functions import TruncMonth
from django.db.models import Q



class Deductibilitate(models.TextChoices):
    DEDUCTIBILA_INTEGRAL = "Deductibila integral", _("Deductibila integral")
    DEDUCTIBILA_INTEGRAL_INVENTAR = "Obiect de inventar (deductibil integral)", _(
        "Obiect de inventar (deductibil integral)"
    )
    DEDUCTIBILA_INTEGRAL_AMORTIZATA = (
        "Mijloc fix peste 2500 RON (ded. integral cu amortizare)",
        _("Mijloc fix peste 2500 RON (ded. integral cu amortizare)"),
    )
    DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI = (
        "Auto, chirii, utilitati 50% din valoarea lor",
        _("Auto, chirii, utilitati 50% din valoarea lor"),
    )
    DEDUCTIBILA_PARTIAL_SPORT_2024 = (
        "Sport, sali de fitness etc. max. 100 EUR pe an",
        _("Sport, sali de fitness etc. max. 100 EUR pe an"),
    )
    DEDUCTIBILA_PARTIAL_PENSIE_PILON_3 = "Pensie pilon III max. 400 EUR pe an", _(
        "Pensie pilon III max. 400 EUR pe an"
    )
    DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT = (
        "Asigurari medicale private max. 400 EUR pe an",
        _("Asigurari medicale private max. 400 EUR pe an"),
    )
    DEDUCTIBILA_PARTIAL_PROTOCOL = "Mese protocol max. 2% baza de calcul", _(
        "Mese protocol max. 2% baza de calcul"
    )
    DEDUCTIBILA_INTEGRAL_SALARII = "Deductibila integral salarii", _(
        "Deductibila integral salarii"
    )
    DEDUCTIBILA_PARTIAL_SOCIALE = (
        "Ajutoare diverse pt. angajati max. 5% din total salarii pe an",
        _("Ajutoare diverse pt. angajati max. 5% din total salarii pe an"),
    )
    DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG = (
        "Contributii obligatorii asociatii, organizatii max. 5% din brut",
        _("Contributii obligatorii asociatii, organizatii max. 5% din brut"),
    )
    DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG = (
        "Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an",
        _("Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an"),
    )


class ModalitateIesireDinUz(models.TextChoices):
    CASAT = "Casat", _("Casat")
    VANDUT = "Vandut", _("Vandut")
    DONAT = "Donat", _("Donat")
    PIERDUT = "Pierdut", _("Pierdut")


class CheltuialaModel(CommonIncasariCheltuieliModel):
    nume_cheltuiala = models.CharField(max_length=10000)
    deductibila = models.CharField(
        max_length=300,
        choices=Deductibilitate,
        default=Deductibilitate.DEDUCTIBILA_INTEGRAL,
    )
    deducere_in_ron = models.FloatField(null=True, blank=True)
    obiect_de_inventar = models.BooleanField(null=True, blank=True, default=False)
    mijloc_fix = models.BooleanField(null=True, blank=True, default=False)
    cod_de_clasificare = models.CharField(max_length=100, null=True, blank=True)
    grupa = models.CharField(max_length=100, null=True, blank=True)
    data_punerii_in_functiune = models.DateField(null=True, blank=True)
    data_amortizarii_complete = models.DateField(null=True, blank=True)
    data_inceperii_amortizarii = models.DateField(null=True, blank=True)
    durata_normala_de_functionare = models.CharField(
        max_length=50, null=True, blank=True
    )
    anul_darii_in_folosinta = models.IntegerField(null=True, blank=True)
    luna_darii_in_folosinta = models.IntegerField(null=True, blank=True)
    anul_amortizarii_complete = models.IntegerField(null=True, blank=True)
    luna_amortizarii_complete = models.IntegerField(null=True, blank=True)
    ani_amortizare = models.IntegerField(null=True, blank=True)
    amortizare_lunara = models.FloatField(null=True, blank=True)
    cota_de_amortizare = models.FloatField(null=True, blank=True)
    scos_din_uz = models.BooleanField(null=True, blank=True, default=False)
    modalitate_iesire_din_uz = models.CharField(
        max_length=300,
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

    def eur_to_ron(self, suma):
        return round((to_ron(1, "EUR", self.data_inserarii) * suma), 2)

    def deducere_suma_fixa_pe_an(
        self, suma_in_eur: int, deductibila_selected: Deductibilitate
    ):

        euro_in_ron = self.eur_to_ron(suma_in_eur)

        result = CheltuialaModel.objects.filter(
            deductibila=deductibila_selected.value,
            data_inserarii__year=self.data_inserarii.year,
        ).aggregate(total_sum=Sum("suma_in_ron"))

        if result["total_sum"] is None:
            total = self.suma_in_ron
        else:
            total = result["total_sum"] + self.suma_in_ron

        if total > euro_in_ron:
            remaining = round((euro_in_ron - (total - self.suma_in_ron)), 2)
            if remaining < 1:
                remaining = 0
            raise ValidationError(
                _(
                    f"Nu putem deduce suma introdusa. Mai sunt {remaining} RON disponibili pentru deducere."
                )
            )

        return self.suma_in_ron

    @staticmethod
    def get_total_cheltuieli_pe_luni(year: int):
        cheltuieli_pe_luni = CheltuialaModel.objects.filter(
            mijloc_fix=False,
            data_inserarii__isnull=False,
            data_inserarii__year=year
        ).annotate(
            month=TruncMonth('data_inserarii')
        ).values('month').annotate(
            tni=Sum('suma_in_ron')
        ).order_by('month')

        data_dict = {entry['month']: entry['tni'] for entry in cheltuieli_pe_luni}

        sume_cheltuieli_pe_luni = {}
        for month in range(1, 13):
            month_date = datetime.date(year, month, 1)
            val_fara_amortizare = data_dict.get(month_date, 0)

            amortizari = CheltuialaModel.objects.filter(
                Q(data_inceperii_amortizarii__lte=month_date) & Q(data_amortizarii_complete__gte=month_date),
                mijloc_fix=True,
            )

            val_amortizari = 0
            for amortizare in amortizari:
                val_amortizari += amortizare.amortizare_lunara

            sume_cheltuieli_pe_luni[month] = val_fara_amortizare + val_amortizari

        return list(sume_cheltuieli_pe_luni.values())


    @staticmethod
    def get_total_cheltuieli(year: int):

        total_cheltuieli_result = CheltuialaModel.objects.filter(
            mijloc_fix=False, data_inserarii__year=year
        ).aggregate(totalc=Sum("deducere_in_ron"))

        if total_cheltuieli_result["totalc"] is None:
            total_cheltuieli = 0
        else:
            total_cheltuieli = total_cheltuieli_result["totalc"]
        
        cheltuieli_mijloc_fix_results = CheltuialaModel.objects.filter(
            Q(data_punerii_in_functiune__year__lte=year) & Q(data_amortizarii_complete__year__gte=year),
            mijloc_fix=True,
        )

        today = timezone.now()
        total_amortizari = 0
        for row in cheltuieli_mijloc_fix_results:
            if year == today.year:
                # pana la luna curenta
                multiply_months = today.month
            elif row.data_inceperii_amortizarii.year == year:
                # 13 pentru ca includem data amortizarii complete 
                multiply_months = 13 - row.data_inceperii_amortizarii.month 
            elif row.data_amortizarii_complete.year == today.year:
                multiply_months = row.data_amortizarii_complete.month - today.month
            else:
                multiply_months = 12
            
            total_amortizari += row.amortizare_lunara * multiply_months

        return round(total_cheltuieli + total_amortizari, 2)

    def calculeaza_deducere_in_ron(self):

        if self.deductibila in [
            Deductibilitate.DEDUCTIBILA_INTEGRAL.value,
            Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII.value,
        ]:
            return self.suma_in_ron

        if self.deductibila == Deductibilitate.DEDUCTIBILA_INTEGRAL_INVENTAR.value:
            self.obiect_de_inventar = True
            return self.suma_in_ron

        if self.deductibila == Deductibilitate.DEDUCTIBILA_INTEGRAL_AMORTIZATA.value:
            clasificare = [
                c
                for c in CODURI_CLASIFICARE
                if c["cod_clasificare"] == self.cod_de_clasificare
            ][0]

            self.mijloc_fix = True
            self.cod_de_clasificare = clasificare["cod_clasificare"]
            self.grupa = clasificare["grupa"]
            self.durata_normala_de_functionare = clasificare["durata_amortizare_in_ani"]
            self.anul_darii_in_folosinta = self.data_punerii_in_functiune.year
            self.luna_darii_in_folosinta = self.data_punerii_in_functiune.month

            if not self.ani_amortizare:
                self.ani_amortizare = int(
                    clasificare["durata_amortizare_in_ani"].split("-")[0]
                )

            self.amortizare_lunara = round((self.suma_in_ron / (self.ani_amortizare * 12)), 2)
            self.cota_de_amortizare = round(
                ((self.amortizare_lunara / self.suma_in_ron) * 100), 2
            )

            self.data_inceperii_amortizarii = (
                self.data_punerii_in_functiune + relativedelta(months=1)
            ).replace(day=1)
            self.data_amortizarii_complete = (
                self.data_punerii_in_functiune
                + relativedelta(years=self.ani_amortizare)
            )

            self.anul_amortizarii_complete = self.data_amortizarii_complete.year
            self.luna_amortizarii_complete = self.data_amortizarii_complete.month

            return self.suma_in_ron

        if (
            self.deductibila
            == Deductibilitate.DEDUCTIBILA_PARTIAL_AUTO_CASA_UTILITATI.value
        ):
            return round((self.suma_in_ron / 2), 2)  # 50%

        if self.deductibila == Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value:
            baza_de_calcul_venit_net = get_venit_net(self.data_inserarii.year)
            suma_admisa_protocol = round(
                baza_de_calcul_venit_net * 0.02, 2
            )  # 2% din baza de calcul

            result = CheltuialaModel.objects.filter(
                deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_PROTOCOL.value,
                data_inserarii__year=self.data_inserarii.year,
            ).aggregate(total_sum=Sum("deducere_in_ron"))

            if result["total_sum"] is None:
                suma_curenta_protocol = self.suma_in_ron
            else:
                suma_curenta_protocol = result["total_sum"] + self.suma_in_ron

            if suma_curenta_protocol > suma_admisa_protocol:
                remaining = round(
                    (suma_admisa_protocol - (suma_curenta_protocol - self.suma_in_ron)),
                    2,
                )
                if remaining < 1:
                    remaining = 0
                raise ValidationError(
                    _(
                        f"Nu putem deduce suma introdusa. Mai sunt {remaining} RON disponibili pentru deducere."
                    )
                )

            return self.suma_in_ron

        if self.deductibila == Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE.value:

            result_salarii = CheltuialaModel.objects.filter(
                deductibila=Deductibilitate.DEDUCTIBILA_INTEGRAL_SALARII.value,
                data_inserarii__year=self.data_inserarii.year,
            ).aggregate(total_s=Sum("deducere_in_ron"))

            if result_salarii["total_s"] is None:
                total_salarii = 0
            else:
                total_salarii = result["total_s"]

            suma_admisa_sociale = round(total_salarii * 0.05, 2)  # 5% din total salarii

            result = CheltuialaModel.objects.filter(
                deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_SOCIALE.value,
                data_inserarii__year=self.data_inserarii.year,
            ).aggregate(total_sum=Sum("deducere_in_ron"))

            if result["total_sum"] is None:
                suma_curenta_sociale = self.suma_in_ron
            else:
                suma_curenta_sociale = result["total_sum"] + self.suma_in_ron

            if suma_curenta_sociale > suma_admisa_sociale:
                remaining = round(
                    (suma_admisa_sociale - (suma_curenta_sociale - self.suma_in_ron)), 2
                )
                if remaining < 1:
                    remaining = 0
                raise ValidationError(
                    _(
                        f"Nu putem deduce suma introdusa. Mai sunt {remaining} RON disponibili pentru deducere."
                    )
                )

            return self.suma_in_ron

        if (
            self.deductibila
            == Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG.value
        ):
            venit_brut = get_venit_brut(self.data_inserarii.year)
            suma_admisa_contrib_asoc_org = round(
                venit_brut * 0.05, 2
            )  # 5% din venit brut

            result = CheltuialaModel.objects.filter(
                deductibila=Deductibilitate.DEDUCTIBILA_PARTIAL_CONTRIBUTII_OBLIGATORII_ASOC_ORG.value,
                data_inserarii__year=self.data_inserarii.year,
            ).aggregate(total_sum=Sum("deducere_in_ron"))

            if result["total_sum"] is None:
                suma_curenta_contrib_asoc_org = self.suma_in_ron
            else:
                suma_curenta_contrib_asoc_org = result["total_sum"] + self.suma_in_ron

            if suma_curenta_contrib_asoc_org > suma_admisa_contrib_asoc_org:
                remaining = round(
                    (
                        suma_admisa_contrib_asoc_org
                        - (suma_curenta_contrib_asoc_org - self.suma_in_ron)
                    ),
                    2,
                )
                if remaining < 1:
                    remaining = 0
                raise ValidationError(
                    _(
                        f"Nu putem deduce suma introdusa. Mai sunt {remaining} RON disponibili pentru deducere."
                    )
                )

            return self.suma_in_ron

        if self.deductibila == Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024.value:
            return self.deducere_suma_fixa_pe_an(
                100, Deductibilitate.DEDUCTIBILA_PARTIAL_SPORT_2024
            )

        if self.deductibila == Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3.value:
            return self.deducere_suma_fixa_pe_an(
                400, Deductibilitate.DEDUCTIBILA_PARTIAL_PENSIE_PILON_3
            )

        if (
            self.deductibila
            == Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT.value
        ):
            return self.deducere_suma_fixa_pe_an(
                400, Deductibilitate.DEDUCTIBILA_PARTIAL_ASIG_MEDICALE_PRIVAT
            )

        if (
            self.deductibila
            == Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG.value
        ):
            return self.deducere_suma_fixa_pe_an(
                4000, Deductibilitate.DEDUCTIBILA_PARTIAL_COTIZATII_VOLUNTARE_ASOC_ORG
            )

    class Meta:
        app_label = "cheltuieli"
        verbose_name_plural = "Cheltuieli"

    def __str__(self):
        return self.deductibila + " " + str(self.deducere_in_ron) + "RON " + self.actualizat_la.isoformat()


CODURI_CLASIFICARE = [
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.1.",
        "denumire_active_fixe": "Cladiri industriale in afara de cladirile din:",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.1.1.",
        "denumire_active_fixe": "- industria alimentara, industria materialelor de constructii, industria metalurgica si industria siderurgica;",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.1.2.",
        "denumire_active_fixe": "- industria chimica.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.2.",
        "denumire_active_fixe": "Constructii usoare cu structuri metalice (hale de productie, hale de montaj, etc.) in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.2.1.",
        "denumire_active_fixe": "- baraci, soproane, etc.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.3.",
        "denumire_active_fixe": "Centrale hidroelectrice, statii si posturi de transformare, statii de conexiuni, in afara de:",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.3.1.",
        "denumire_active_fixe": "- constructii speciale metalice;",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.3.2.",
        "denumire_active_fixe": "- constructii speciale din beton",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.4.",
        "denumire_active_fixe": "Centrale termoelectrice si nuclearo-electrice, in afara de:",
        "durata_amortizare_in_ani": "30-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.4.1.",
        "denumire_active_fixe": "- cladirea reactorului",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.5.1.",
        "denumire_active_fixe": "- din beton;",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.5.2.",
        "denumire_active_fixe": "- din balast, macadam.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.6.1.",
        "denumire_active_fixe": "- sonde de titei, gaze si sare",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.6.2.",
        "denumire_active_fixe": "- platforme marine de foraj si extractie",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.7.",
        "denumire_active_fixe": "Turnuri de extractie miniera.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.8.",
        "denumire_active_fixe": "Puturi de mina, galerii, planuri inclinate si rampe de put.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.9.",
        "denumire_active_fixe": "Structuri de sustinere, estacade si culoare pentru transportoare cu banda.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.10.",
        "denumire_active_fixe": "Rampe de incarcare-descarcare.",
        "durata_amortizare_in_ani": "25-35",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.11.",
        "denumire_active_fixe": "Constructii miniere subterane: pentru personal; gari si remize; statii de pompare; statii de compresoare; canale pentru aeraj; buncare; suitori-coboratori; etc.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.12.",
        "denumire_active_fixe": "Cosuri de fum si turnuri de racire",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.13.",
        "denumire_active_fixe": "Iazuri pentru decantarea sterilului",
        "durata_amortizare_in_ani": "12-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.14.",
        "denumire_active_fixe": "Camere de fum, de desprafuire, de uscare.",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.15.",
        "denumire_active_fixe": "Lucrari de constructii de decoperta pentru exploatari miniere",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.16.",
        "denumire_active_fixe": "Poligoane de incercari experimentale in aer liber sau in incaperi inchise.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.1.17.",
        "denumire_active_fixe": "Alte constructii industriale neregasite in cadrul subgrupei 1.1.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.1.",
        "denumire_active_fixe": "Cladiri agrozootehnice",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.2.",
        "denumire_active_fixe": "Constructii agricole usoare (baraci, magazii, soproane, cabane)",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.3.",
        "denumire_active_fixe": "Depozite de ingrasaminte minerale sau naturale (constructii de compostare).",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.4.",
        "denumire_active_fixe": "Silozuri pentru furaje",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.5.",
        "denumire_active_fixe": "Silozuri pentru depozitarea si conservarea cerealelor.",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.6.",
        "denumire_active_fixe": "Patule pentru depozitarea porumbului.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.7.",
        "denumire_active_fixe": "Constructii pentru cresterea animalelor si pasarilor, padocuri.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.8.",
        "denumire_active_fixe": "Helestee, iazuri, bazine; ecluze si ascensoare; baraje; jgheaburi etc. pentru piscicultura.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.9.",
        "denumire_active_fixe": "Terase pe arabil, plantatii pomicole si viticole.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.10.1.",
        "denumire_active_fixe": "- din zidarie, beton, metal sau lemn si sticla.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.10.2.",
        "denumire_active_fixe": "- constructie usoara din lemn si folie din masa plastica.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.2.11.",
        "denumire_active_fixe": "Alte constructii agricole neregasite in cadrul subgrupei 1.2.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.1.",
        "denumire_active_fixe": "Cladiri pentru transporturi: autogari, gari, statii pentru metrou, aeroporturi, porturi, hangare, depouri, garaje, ateliere, in afara de:",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.1.1.",
        "denumire_active_fixe": "- cladiri usoare cu structura metalica",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.2.1.",
        "denumire_active_fixe": "- ecartament normal si larg.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.2.2.",
        "denumire_active_fixe": "- ecartament normal pentru metrou.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.2.3.",
        "denumire_active_fixe": "- ecartament ingust, inclusiv forestier.",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.2.4.",
        "denumire_active_fixe": "- ecartament ingust minier.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.3.",
        "denumire_active_fixe": "Infrastructura si statii de tramvaie.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.4.1.",
        "denumire_active_fixe": "- pentru linii de cale ferata.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.4.2.",
        "denumire_active_fixe": "- pentru linii de tramvaie si troleibuze.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.4.3.",
        "denumire_active_fixe": "- pentru linii de cale ferata miniera.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.5.",
        "denumire_active_fixe": "Constructii pentru transport feroviar: peroane; treceri de nivel; port-gabarit; cheiuri de incarcare-descarcare; pentru alimentare si revizie locomotive; canale de coborat osii; fundatii de placi turnante si pod bascula; canale de zgura, etc.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.6.",
        "denumire_active_fixe": "Aparate de cale.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.7.1.",
        "denumire_active_fixe": "- cu imbracaminte din balast, pamant stabilizat sau macadam.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.7.2.",
        "denumire_active_fixe": "- cu imbracaminte din beton asfaltic sau pavaj pe fundatie supla.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.7.3.",
        "denumire_active_fixe": "- cu imbracaminte din beton de ciment.",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.7.4.",
        "denumire_active_fixe": "- Infrastructura drumuri forestiere",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.8.",
        "denumire_active_fixe": "Piste pentru aeroporturi si platforme de stationare pentru avioane si autovehicule. Constructii aeroportuare.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.9.",
        "denumire_active_fixe": "Cheiuri, estacade si docuri pentru nave.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.10.1.",
        "denumire_active_fixe": "- File din lemn.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.10.2.",
        "denumire_active_fixe": "- File din beton, beton armat.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.11.",
        "denumire_active_fixe": "Canale pentru navigatie.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.12.",
        "denumire_active_fixe": "Constructii accesorii pentru transport rutier, aerian, naval.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.13.1.",
        "denumire_active_fixe": "- pe stalpi din lemn.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.13.2.",
        "denumire_active_fixe": "- pe stalpi din metal sau beton armat.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.14.1.",
        "denumire_active_fixe": "- cu telecabine, telegondole sau teleschiuri.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.14.2.",
        "denumire_active_fixe": "- multilifturi pentru schi.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.15.",
        "denumire_active_fixe": "Linii funiculare forestiere de tip usor.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.16.",
        "denumire_active_fixe": "Planuri inclinate supraterane.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.17.1.",
        "denumire_active_fixe": "- din lemn.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.17.2.",
        "denumire_active_fixe": "- din zidarie, beton armat sau metal.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.18.",
        "denumire_active_fixe": "Tunele.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.19.",
        "denumire_active_fixe": "Cladiri pentru posta, telecomunicatiixentrale telefonice, statii de emisie radio, studiouri pentru radio, televiziune, etc.",
        "durata_amortizare_in_ani": "36-54",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.20.",
        "denumire_active_fixe": "Linii si cabluri aeriene de telecomunicatii (stalpi, circuite, cabluri, traverse, console, etc.).",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.21.",
        "denumire_active_fixe": "Retele si canalizatii subterane de comunicatii urbane si interurbane, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.21.1.",
        "denumire_active_fixe": "- Suport de transmisiuni de telecomunicatii pe sisteme de cabluri cu fibra optica (submarine, subfluviale).",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.22.",
        "denumire_active_fixe": "Platforme, turnuri si piloni metalici pentru antene de radiotelefonie, telefonie mobila, radio si TV.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.23.",
        "denumire_active_fixe": "Cabine telefonice.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.24.",
        "denumire_active_fixe": "Constructii usoare pentru transporturi si telecomunicatii (baraci, magazii, soproane, cabane).",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.3.25.",
        "denumire_active_fixe": "Alte constructii pentru transporturi, posta si telecomunicatii neregasite in cadrul subgrupei 1.3.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.1.",
        "denumire_active_fixe": "Baraje si constructii accesorii baraje (ecluze, deversoare, porturi si fronturi de asteptare, disipatoare de energie, goliri de fund, canale de derivatie).",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.2.1.",
        "denumire_active_fixe": "- din fascine; lemn cu bolovan sau piatra;",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.2.2.",
        "denumire_active_fixe": "- din piatra bruta; blocuri de beton; zidarie de piatra; beton armat.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.3.",
        "denumire_active_fixe": "Canale de aductiune.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.4.",
        "denumire_active_fixe": "Pereuri.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.5.",
        "denumire_active_fixe": "Constructii hidrotehnice, hidrometrice, hidrometeorologice, oceanografice, platforme meteorologice; in afara.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.5.1.",
        "denumire_active_fixe": "- constructii usoare.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.6.",
        "denumire_active_fixe": "Lacuri artificiale de acumulare",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.4.7.",
        "denumire_active_fixe": "Alte constructii hidrotehnice neregasite in cadrul subgrupei 1.4.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.1.",
        "denumire_active_fixe": "Centre de afaceri.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.2.",
        "denumire_active_fixe": "Cladiri comerciale pentru depozitare-comercializare si distributie. Magazine.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.3.",
        "denumire_active_fixe": "Constructii pentru depozitarea marfurilor de larg consum, a marfurilor industriale, a materialelor de constructii si a produselor",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.4.",
        "denumire_active_fixe": "Constructii pentru depozitarea si comercializarea produselor petrolifere (benzinarii, etc.).",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.5.",
        "denumire_active_fixe": "Constructii pentru depozitarea explozibililor, carburantilor si lubrifiantilor.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.6.",
        "denumire_active_fixe": "Silozuri pentru agregate minerale, minereuri, carbuni, materiale pulverulente (ciment, var, ipsos), etc.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.7.",
        "denumire_active_fixe": "Rezervoare si bazine pentru depozitare, in afara de:",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.7.1.",
        "denumire_active_fixe": "- rezervoare pentru depozitare cu protectie catodica",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.8.",
        "denumire_active_fixe": "Depozite frigorifice pentru alimente. Ghetarii.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.9.",
        "denumire_active_fixe": "Platforme pentru depozitare si activitati comerciale.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.10.",
        "denumire_active_fixe": "Tancuri, rezervoare, bidoane si butoaie pentru depozitarea bauturilor.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.11.",
        "denumire_active_fixe": "Rampe de incarcare.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.12.",
        "denumire_active_fixe": "Constructii usoare pentru afaceri, comert, depozitare (baraci, magazii, soproane, etc.).",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.13.",
        "denumire_active_fixe": "Camere de tezaur pentru depozitarea valorilor si datelor.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.5.14.",
        "denumire_active_fixe": "Alte constructii pentru afaceri, comert, depozitare neregasite in cadrul subgrupei 1.5.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.1.",
        "denumire_active_fixe": "Cladiri de locuit, hoteluri si camine, in afara de:",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.1.1.",
        "denumire_active_fixe": "- cladiri pentru locuinte sociale, moteluri si camine amplasate in centre industriale. WC publice.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.2.",
        "denumire_active_fixe": "Constructii pentru invatamant; stiinta; cultura si arta; ocrotirea sanatatii; asistenta sociala; cultura fizica si agrement, in afara de:",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.2.1.",
        "denumire_active_fixe": "- case de sanatate, bai publice si baze de tratament.",
        "durata_amortizare_in_ani": "28-42",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.3.1.",
        "denumire_active_fixe": "- lemn;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.3.2.",
        "denumire_active_fixe": "- zidarie, beton armat, metal.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.4.",
        "denumire_active_fixe": "Cladiri administrative.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.5.",
        "denumire_active_fixe": "Constructii pentru centrale termice si puncte termice",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.6.",
        "denumire_active_fixe": "Constructii suport pentru panouri de afisare si publicitate.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.7.",
        "denumire_active_fixe": "Constructii pentru turnuri de ceas, turnuri de paza si alte amenajari asemanatoare.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.6.8.",
        "denumire_active_fixe": "Alte constructii de locuinte si social-culturale neregasite in cadrul subgrupei 1.6.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.1.1.",
        "denumire_active_fixe": "- aeriene pe stalpi din lemn.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.1.2.",
        "denumire_active_fixe": "- aeriene pe stalpi metalici sau din beton armat.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.1.3.",
        "denumire_active_fixe": "- subterane.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.2.1.",
        "denumire_active_fixe": "- aeriene sau aparente.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.2.2.",
        "denumire_active_fixe": "- ingropate.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.2.3.",
        "denumire_active_fixe": "- in tub, canal sau tunel de protectie.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.7.3.",
        "denumire_active_fixe": "Alte constructii pentru transportul energiei electrice neregasite in cadrul subgrupei 1.7.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.1.",
        "denumire_active_fixe": "Puturi sapate sau forate.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.2.",
        "denumire_active_fixe": "Drenuri pentru alimentari cu apa.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.3.",
        "denumire_active_fixe": "Captari si prize de apa.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.4.",
        "denumire_active_fixe": "Canale pentru alimentare cu apa si evacuarea apelor.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.5.",
        "denumire_active_fixe": "Galerii pentru alimentare cu apa si evacuarea apelor.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.6.",
        "denumire_active_fixe": "Conducte pentru alimentare cu apa, inclusiv traversarile; retele de distributie. Galerii subterane pentru instalatii tehnico-edilitare.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.7.",
        "denumire_active_fixe": "Conducte pentru canalizare, in afara de:",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.7.1.",
        "denumire_active_fixe": "- conducte tehnologice pentru ape acide.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.8.",
        "denumire_active_fixe": "Statii de tratare, de neutralizare si de epurare a apelor.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.9.",
        "denumire_active_fixe": "Castele de apa.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.10.",
        "denumire_active_fixe": "Iazuri de depozitare; paturi de uscare a namolului; campuri de irigare si infiltrare, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.10.1.",
        "denumire_active_fixe": "- canale de irigatii.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.11.",
        "denumire_active_fixe": "Rezervoare din beton armat pentru inmagazinarea apei.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.12.",
        "denumire_active_fixe": "Statii de pompare si separare a apei, in afara de:",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.12.1.",
        "denumire_active_fixe": "- statii de pompare plutitoare",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.13.",
        "denumire_active_fixe": "Constructii si instalatii tehnologice pentru alimentare cu apa si canalizare.",
        "durata_amortizare_in_ani": "32-48",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.14.",
        "denumire_active_fixe": "Constructii usoare (baraci, magazii, soproane, etc.).",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.8.15.",
        "denumire_active_fixe": "Alte constructii pentru alimentare cu apa, canalizare si imbunatatiri funciare neregasite in cadrul subgrupei 1.8.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.1.",
        "denumire_active_fixe": "Conducte magistrale pentru transportul produselor petrolifere, gazelor si a lichidelor industriale, inclusiv traversarile si instalatiile tehnologice, in afara de:",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.1.1.",
        "denumire_active_fixe": "- conducte magistrale pentru transportul produselor petroliere prevazute cu protectie catodica.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.2.1.",
        "denumire_active_fixe": "- aeriene sau in canale de protectie vizitabile.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.2.2.",
        "denumire_active_fixe": "- in canale nevizitabile.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.3.",
        "denumire_active_fixe": "Conducte, bransamente si instalatii tehnologice pentru distributia gazelor, produselor petroliere si a lichidelor industriale, apa sarata, din exteriorul si interiorul constructiilor.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.9.4.",
        "denumire_active_fixe": "Alte constructii pentru transportul si distributia petrolului, gazelor,",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 1. CONSTRUCTII",
        "cod_clasificare": "1.10.",
        "denumire_active_fixe": "Alte constructii neregasite in cadrul grupei 1.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru constructia puturilor miniere si forare miniera.  Masini de havat, combine miniere si pluguri de carbune.  Masini multifunctionale pe senile.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru sustinerea abatajelor si pentru taiere-prelucrare.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.3.",
        "denumire_active_fixe": "Masini de incarcat si utilaje pentru rambleiere.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.4.",
        "denumire_active_fixe": "Excavatoare cu rotor si instalatii de haldat. Masini, utilaje si instalatii de sfaramare si macinare.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru clasare; pentru separare si concentrare (gravimetrica, magnetica, electrostatica).  Masini, utilaje si instalatii pentru flotatie.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.6.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru extragerea si prepararea metalelor pretioase.  Masini de tabletat si brichetat sare. Masini si utilaje pentru brichetarea carbunilor",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.7.",
        "denumire_active_fixe": "Masini de ascutit sfredele si masini de curatat vagonete.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.1.8.",
        "denumire_active_fixe": "Alte echipamente tehnologice neregasite in cadrul clasei 2.1.1.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.2.1.",
        "denumire_active_fixe": "Sondeze",
        "durata_amortizare_in_ani": "7-11",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.2.2.",
        "denumire_active_fixe": "Utilaje si instalatii pentru forajul sondelor de titei si gaze",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.2.3.",
        "denumire_active_fixe": "Trepiede, turle metalice, geamblacuri, macarale, trolii si mese rotative.  Agregate de cimentare si fisurare.  Masini, utilaje si instalatii pentru extractia titeiului si gazelor.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.2.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru carotaj, deviatii si perforari",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.2.5.",
        "denumire_active_fixe": "Alte echipamente tehnologice neregasite in cadrul clasei 2.1.2.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.3.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru productia de cocs metalurgic; pentru productia fontei de prima fuziune si a feroaliajelor.  Masini, utilaje si instalatii pentru productia electrozilor de sudura.  Masini, utilaje si instalatii pentru acoperirea si protectia suprafetei laminatelor, tevilor si trefilatelor.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.3.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru productia de otel.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.3.3.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru productia de laminate.  Masini, utilaje si instalatii pentru productia barelor, sarmelor si tevilor trase.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.3.4.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.3.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.4.1.",
        "denumire_active_fixe": "Masini si instalatii pentru reducere, topire, distilare si turnare. Cuptoare pentru prerafinare; masini si instalatii pentru convertizoare si rafinare.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.4.2.",
        "denumire_active_fixe": "Masini si instalatii pentru prelucrarea produselor, subproduselor si deseurilor din metalurgia neferoasa.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.4.3.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.4.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.1.",
        "denumire_active_fixe": "Masini de alezat si frezat orizontale. Masini de rabotat cu masa mobila.  Ciocane de forja.  Prese de forja; prese speciale si specializate; masini de forjat; masini de rulat, indoit si debitat tabla, profile si tevi; masini auxiliare speciale pentru forja.  Masini si instalatii de incalzire pentru forja.  Masini, utilaje si instalatii pentru dezbaterea si curatirea pieselor turnate.  Masini, utilaje si instalatii pentru tratamente termice.  Masini, utilaje si instalatii specifice pentru productia de cabluri si conductoare.  Masini, utilaje si instalatii specifice pentru productia de materiale electroizolante si de pulberi.  Masini, utilaje si instalatii specializate de confectionat produse din sarma (cuie, ace, tinte, etc.).  Masini, utilaje si instalatii specializate de confectionat produse din tabla subtire (jucarii, ambalaje, etc.,).  Masini, utilaje si instalatii specializate de confectionat autovehicule, tractoare, locomotive, vagoane.  Masini specializate pentru confectionat nituri, suruburi, tirfoane, piulite si caiele.  Masini, utilaje si instalatii specializate pentru constructia de nave, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.1.1.",
        "denumire_active_fixe": "Linii automate de formare-turnare.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.2.",
        "denumire_active_fixe": "Strunguri:  - paralele;  - frontale si carusel;  - revolver, automate si semiautomate;  - specializate. Masini de alezat.  Masini de frezat.  Masini de rabotat cu cutit mobil (sepinguri) si de mortezat, de prelucrat roti dintate, de filetat, etc., polizoare fixe.  Masini de gaurit, masini de debitat metale.  Masini agregat; linii automate si semiautomate; centre de prelucrare a metalului prin aschiere.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.3.",
        "denumire_active_fixe": "Masini specializate pentru confectionat arcuri.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specializate pentru confectionarea ceasurilor.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru sudarea metalului.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.6.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice pentru productia componentelor produselor si sistemelor electronice (semiconductoare, circuite imprimate, aparate audio si video, aparate si instrumente electronice de masurare, calculatoare si periferice, etc.).",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.7.",
        "denumire_active_fixe": "Masini portabile de polizat, slefuit, taiat, gaurit, etc.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.5.8.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.5.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.1.1.",
        "denumire_active_fixe": "b) mediu puternic coroziv",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.1.2.",
        "denumire_active_fixe": "a) mediu neutru sau usor coroziv;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.2.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice pentru producerea acidului sulfuric si a ingrasamintelor fosfatice, a amoniacului, acidului azotic si a ingrasamintelor azotoase. Masini, utilaje si instalatii specifice producerii sodei;  Masini, utilaje si instalatii specifice producerii carbidului oxigenului, pulberilor si explozibililor.  Alte masini, utilaje si instalatii specifice pentru industria chimica anorganica.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.2.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice producerii clorului si a compusilor sai.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.3.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice producerii fibrelor si firelor artificiale.  Vase pentru coagularea latexului, prese de turnare, masini automate de ambalare in baloturi si masini de turnat epruvete de cauciuc.  Masini, utilaje si instalatii specializate pentru confectionat produse din cauciuc (anvelope, garnituri, tuburi, etc.)",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.3.2.",
        "denumire_active_fixe": "Granulatoare pentru negru de fum. Reactoare pentru dehidrogenarea butanului; polimerizatoare.  Masini, utilaje si instalatii specializate pentru confectionat produse din mase plastice.  Masini, utilaje si instalatii specializate pentru producerea medicamentelor.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.3.3.",
        "denumire_active_fixe": "Instalatii pentru preparat solutii, in circuit inchis, in vase de sticla si vase de cuart pentru filtrare.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.3.4.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii pentru industria chimica organica.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice prelucrarii titeiului, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.4.1.",
        "denumire_active_fixe": "- coloane de distilare fractionata si generatoare de gaz inert; - vase pentru propan si butan;",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.4.2.",
        "denumire_active_fixe": "- agregate pentru taierea hidraulica a cocsului, regeneratoare de catalizator si umectoare: coloane pentru recuperarea SO2 din rafinat si coloane de solventare cu bioxid de sulf si cuptoare pentru arderea gudroanelor;",
        "durata_amortizare_in_ani": "7-11",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice productiei de sapun, detergenti si lumanari.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.6.6.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.6.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru fasonarea produselor, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.1.1.",
        "denumire_active_fixe": "- masini de fasonat prin presare; - masini de fasonat prin laminare;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru uscarea produselor. Masini, utilaje si instalatii pentru maturizarea produselor.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.3.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru arderea produselor, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.3.1.",
        "denumire_active_fixe": "- cuptoare electrice pentru elaborarea electro-corindonului si a carbuni de siliciu precum si pentru ars email.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru deservirea uscatoriilor si cuptoarelor.  Masini si instalatii specifice pentru producerea cimentului, varului si a ipsosului.  Masini si instalatii specifice fabricarii produselor din azbociment.  Masini, utilaje si instalatii specifice producerii materialelor hidroizolatoare (carton asfaltat, etc.).  Masini si instalatii specifice producerii materialelor termoizolatoare (a vatei minerale, a vatei si paslei din fibre de sticla).  Masini si instalatii specifice producerii garniturilor tehnice de etansare.  Masini si instalatii specifice producerii rondelelor, placilor izolatoare si dopurilor din pluta.  Masini si instalatii specifice pentru extragerea si prelucrarea marmurei si a pietrei naturale si artificiale de constructii.  Masini, utilaje si instalatii specifice pentru ambalarea produselor.  Masini si instalatii specifice pentru prefabricate din beton, caramizi silico-calcare si tigle din ciment, in afara de:",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.4.1.",
        "denumire_active_fixe": "- tipare metalice si de beton, incalzitoare; - casete verticale.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.4.2.",
        "denumire_active_fixe": "- tipare pentru tuburi din beton.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.7.5.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.7.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.1.",
        "denumire_active_fixe": "Masini de cojit, despicat, tocat si maruntit. Strunguri si masini de copiat. Ferastraie, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.1.1.",
        "denumire_active_fixe": "- ferastraie cu lant portabile",
        "durata_amortizare_in_ani": "2-3",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.2.",
        "denumire_active_fixe": "Masini de rindeluit, de frezat, de gaurit si daltuit, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.2.1.",
        "denumire_active_fixe": "- masini portabile de rindeluit, de frezat, de gaurit si daltuit.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.3.",
        "denumire_active_fixe": "Masini de slefuit, de lustruit, masini combinate, masini agregat, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.3.1.",
        "denumire_active_fixe": "- masini portabile de slefuit si de lustruit.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.4.",
        "denumire_active_fixe": "Masini-unelte pentru prelucrarea lemnului prin taiere si masini de curbat; agregate de innadire si asamblare; prese specifice pentru industria lemnului; masini, utilaje si instalatii pentru preparat si aplicat adezivi si lacuri, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.4.1.",
        "denumire_active_fixe": "- masini portabile de taiat si de imbinat prin agrafe, cuie, clame.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru uscare, aburire si tratare termica, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.5.1.",
        "denumire_active_fixe": "- masini si instalatii de aburire si fierbere a lemnului.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.6.",
        "denumire_active_fixe": "Masini, utilaje si instalatii specifice liniilor de fabricatie pentru prelucrarea lemnului.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.7.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru silvicultura.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.8.8.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.8.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru fabricarea celulozei, in afara de:",
        "durata_amortizare_in_ani": "10-16",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.1.1.",
        "denumire_active_fixe": "- putini din lemn pentru spalare.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.2.",
        "denumire_active_fixe": "Masini si instalatii pentru fabricarea hartiei, cartonului si mucavalei. Masini si utilaje pentru impregnarea si innobilarea hartiei si cartoanelor.  Utilaje pentru exploatarea si balotarea stufului, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.2.1.",
        "denumire_active_fixe": "- tractoare speciale pentru recoltat stuf; - recoltatoare de stuf.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.3.",
        "denumire_active_fixe": "Masini si utilaje pentru confectii din hartie si prelucrarea hartiei.",
        "durata_amortizare_in_ani": "10-16",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.9.4.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.9.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.10.1.",
        "denumire_active_fixe": "Cuptoare pentru producerea masei de sticla si tratarea produselor din sticla; masini de format si de prelucrat sticla, in afara de:",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.10.1.1.",
        "denumire_active_fixe": "- cuptoare de topire cu oale; de curbat si de securizat geamuri;  - masini de confectionat aparatura de sticla pentru laborator, masini de gradat, masini de spart geamuri armate, de indreptat tuburi din sticla, de inchis termometre, de spalat cioburi, piese de rondele pentru masinile de tras geam;  - masini de format materiale ceramice;  - masini si instalatii de finisat si decorat produse din sticla si ceramica fina.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.10.2.",
        "denumire_active_fixe": "Masini de ambalat butelii, de spalat si stors panza de filtru, instalatii de dozarea barbotinei, etc.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.10.3.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.10.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.11.1.",
        "denumire_active_fixe": "Masini pentru prelucrarea primara a fibrelor naturale.  Masini, utilaje si instalatii pentru prelucrarea primara a fibrelor de lana si a parului. Masini pentru prelucrarea preliminara a deseurilor din fibre si a zdrentelor.  Masini si instalatii din filaturile de bumbac.",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.11.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii din filaturile de matase naturala.  Masini, utilaje si instalatii din filaturile de fibre liberiene si din filaturile de lana. Masini si utilaje pentru prepararea firelor.  Masini, utilaje si instalatii pentru produs materiale textile netesute si electroplus. Masini pentru pregatire in vederea tratamentelor si finisarii.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.11.3.",
        "denumire_active_fixe": "Masini si instalatii de albit.  Masini si instalatii pentru tratamente umede fara folosire de coloranti.  Masini de stors si de uscat materiale textile.  Masini si instalatii pentru apretura si finisarea speciala a materialelor textile; de controlat, ajustat si impachetat.  Masini de tesut.",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.11.4.",
        "denumire_active_fixe": "Masini de tricotat; de impletit, crosetat si innodat.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.11.5.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.11.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.12.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru industria confectiilor",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.13.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru produs talpa artificiala.  Masini, utilaje si instalatii pentru confectii de incaltaminte din piele si din inlocuitori din piele.  Masini, utilaje si instalatii pentru confectionarea incaltamintei din cauciuc; pentru confectii de: manusi, blanarie, marochinarie si articole tehnice din piele.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.13.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru tabacarii, in afara de:",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.13.2.1.",
        "denumire_active_fixe": "- bazine de inmuiat, cenusarit, pretabacit, tabacit si decolorat.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.13.2.2.",
        "denumire_active_fixe": "- haspele de inmuiat, cenusarit, decalcifiat, semaluire, pielat, tabacit si argasit si butoaie de inmuiat, cenusarit, decalcifiat, semaluire, pielat, tabacit, vopsit, retanat, uns, valcuit, etc.; agregate elicoidale de cenusarit si tabacit.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.13.3.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.13.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.1.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru abatoare si producerea preparatelor din carne.",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru lapte si produse lactate.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.3.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru producerea uleiurilor vegetale si a margarinei; panificatie si producerea pastelor fainoase si a biscuitilor.  Masini, utilaje si instalatii pentru producerea spirtului, amidonului, glucozei, dextrinei si drojdiei comprimate.  Masini si instalatii pentru producerea tuicii, rachiurilor naturale, altor bauturi distilate si gazoase, esentelor si otetului.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru ambalarea produselor alimentare.  Masini, utilaje si instalatii pentru producerea conservelor de legume si fructe.  Masini, utilaje si instalatii comune pentru industria alimentara.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru morarit.",
        "durata_amortizare_in_ani": "13-21",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.6.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru producerea zaharului.",
        "durata_amortizare_in_ani": "14-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.7.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru producerea produselor zaharoase.  Masini, utilaje si instalatii pentru producerea vinului.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.8.",
        "denumire_active_fixe": "Inventar gospodaresc din industria alimentara.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.14.9.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.14.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.15.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru industria poligrafica",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.1.",
        "denumire_active_fixe": "Masini generatoare, in afara de:",
        "durata_amortizare_in_ani": "22-34",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.1.1.",
        "denumire_active_fixe": "- instalatii de preparare a prafului de carbune, instalatii de tratare a apei de alimentare, instalatii de captare si evacuare a zgurei si cenusii;",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.1.2.1.",
        "denumire_active_fixe": "- generatoare de curent continuu, de curent alternativ; generatoare de frecventa",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.1.2.2.",
        "denumire_active_fixe": "- grupuri electrogene stationare",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.1.2.3.",
        "denumire_active_fixe": "- grupuri electrogene mobile, grupuri de sudura mobile",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.2.1.",
        "denumire_active_fixe": "- motoare electrice de curent continuu si de curent alternativ;",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.2.2.",
        "denumire_active_fixe": "- turbine cu abur, turbine cu gaze;",
        "durata_amortizare_in_ani": "12-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.2.3.",
        "denumire_active_fixe": "- turbine hidraulice;",
        "durata_amortizare_in_ani": "12-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.2.4.",
        "denumire_active_fixe": "- motoare cu ardere interna, cu piston, stabile;",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.2.5.",
        "denumire_active_fixe": "- motoare eoliene.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.1.",
        "denumire_active_fixe": "- transformatoare si autotransformatoare, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.1.1.",
        "denumire_active_fixe": "- transformatoare si autotransformatoare de sudura.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.1.2.",
        "denumire_active_fixe": "- aparate de sudura electrica portabile.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.2.",
        "denumire_active_fixe": "- instalatii de redresare; - instalatii de convertizoare, in afara de:",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.2.1.",
        "denumire_active_fixe": "- roboti de pornire mobili",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.3.",
        "denumire_active_fixe": "- baterii de acumulatoare; instalatii de compensare a puterii reactive;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.3.4.",
        "denumire_active_fixe": "- baterii de acumulatoare pentru telecomunicatii.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.4.1.",
        "denumire_active_fixe": "- compresoare cu piston, stabile.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.4.2.",
        "denumire_active_fixe": "- compresoare cu piston, mobile.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.4.3.",
        "denumire_active_fixe": "- compresoare rotative, elicoidale, cu pistoane rotative, rotative cu inel de lichid si centrifuge, stabile.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.4.4.",
        "denumire_active_fixe": "- compresoare rotative, elicoidale, cu pistoane rotative, rotative cu inel de lichid si centrifuge, mobile.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.4.5.",
        "denumire_active_fixe": "- pompe de vid.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.5.",
        "denumire_active_fixe": "Aparataje pentru statii electrice si posturi de transformare.  Echipamente pentru centrale termice, electrice si nucleare.",
        "durata_amortizare_in_ani": "8-30",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.16.6.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.16.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.1.",
        "denumire_active_fixe": "- pompe centrifuge, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.1.1.",
        "denumire_active_fixe": "- pentru lichide slab corozive;",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.1.2.",
        "denumire_active_fixe": "- pentru lichide cu actiune coroziva sau abraziva",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.1.3.",
        "denumire_active_fixe": "- pentru titei.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.2.",
        "denumire_active_fixe": "- pompe axiale; - pompe de injectie; - pompe cu roti dintate; - aparate si dispozitive pentru vehicularea lichidelor.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.3.1.",
        "denumire_active_fixe": "- pentru lichide necorozive;",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.3.2.",
        "denumire_active_fixe": "- pentru lichide cu actiune abraziva si coroziva;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.3.3.",
        "denumire_active_fixe": "- pentru extractia titeiului.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.4.",
        "denumire_active_fixe": "- pompe cu pistonase, pompe cu membrana si pompe elicoidale, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.1.4.1.",
        "denumire_active_fixe": "- pompe de adancime cu cavitati progresive pentru extractia titeiului.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.2.",
        "denumire_active_fixe": "Masini si utilaje comune pentru prelucrarea mecanica a pamanturilor, minereurilor si a altor materii prime;  Concasoare, delaioare si dezintegratoare;  Ciururi si site;  Alte masini si utilaje (roti desecatoare, gratare de separare, clasoare);  Masini de echilibrat;  Mori, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.2.1.",
        "denumire_active_fixe": "- morile din industria cimentului.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.3.",
        "denumire_active_fixe": "Ventilatoare, aeroterme si microcentrale termice murale sau de pardoseli, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.3.1.",
        "denumire_active_fixe": "- aparate de climatizare.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.4.",
        "denumire_active_fixe": "b) mediu puternic coroziv.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.5.",
        "denumire_active_fixe": "b) mediu puternic coroziv;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.6.",
        "denumire_active_fixe": "Masini si instalatii pentru industria frigului.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.17.7.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.17.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.18.",
        "denumire_active_fixe": "Utilaje specifice productiei de electrozi din grafit.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.19.",
        "denumire_active_fixe": "Unelte, dispozitive, instrumente si truse de scule specializate folosite in industrie.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.1.",
        "denumire_active_fixe": "Masini si utilaje pentru saparea si pregatirea terenului.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.1.1.",
        "denumire_active_fixe": "- excavatoare de peste 150 kW.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.2.",
        "denumire_active_fixe": "Masini si utilaje pentru lucrari de fundatii, lucrari in stanca si pentru tuneluri; Instalatii de forat la sectiune plina;  Berbeci mecanici si extractoare de piloti; Utilaje pentru executarea lucrarilor sub apa si masini de forat si turnat piloti, in afara de:",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.2.1.",
        "denumire_active_fixe": "- sonete.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.2.2.",
        "denumire_active_fixe": "- ciocane pneumatice.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.2.3.",
        "denumire_active_fixe": "- scuturi.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.3.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru prepararea, transportul si punerea in opera a betonului si mortarului, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.3.1.",
        "denumire_active_fixe": "- betoniere si malaxoare, autobetoniere, pompe si autopompe de beton;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.3.2.",
        "denumire_active_fixe": "- centrale de beton;",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.3.3.",
        "denumire_active_fixe": "- vibratoare de interior si de exterior pentru compactarea betonului.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru lucrari de zidarie, tencuieli, finisaje, izolatii si instalatii, in afara de:",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.4.1.",
        "denumire_active_fixe": "- unelte mecanice portabile (electrice, pneumatice, hidraulice);",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru lucrari hidrotehnice, in afara de:",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.5.1.",
        "denumire_active_fixe": "- dragi;",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.5.2.",
        "denumire_active_fixe": "- greifere plutitoare;",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.5.3.",
        "denumire_active_fixe": "- elevatoare.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.6.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru constructii si reparatii de drumuri, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.6.1.",
        "denumire_active_fixe": "- compactoare tractate si autopropulsate vibratoare si mixte, masini de taiat asfalt, placi vibratoare si maiuri mecanice.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru constructii si reparatii de cai ferate, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.1.",
        "denumire_active_fixe": "- ciocane de burat prin vibrare;",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.2.",
        "denumire_active_fixe": "- masini de burat;",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.3.",
        "denumire_active_fixe": "- utilaje pentru indreptat si indoit sine;",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.4.",
        "denumire_active_fixe": "- masini pentru montarea si sudarea sinei;",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.7.5.",
        "denumire_active_fixe": "- masini pentru pozarea caii, utilaje de masurat si verificat cale si masini de rectificat rosturi.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.8.",
        "denumire_active_fixe": "Masini pentru executarea armaturilor pentru beton.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.9.",
        "denumire_active_fixe": "Masini si utilaje pentru lucrari de conducte magistrale si linii de transport electrice.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.10.",
        "denumire_active_fixe": "Unelte, dispozitive si instrumente folosite in constructii.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.20.11.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.20.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.1.1.",
        "denumire_active_fixe": "- tractoare agricole; - masini pentru administrarea ingrasamintelor, aparate si dispozitive pentru tratarea culturilor (stropit, prafuit).",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.1.2.",
        "denumire_active_fixe": "- utilaje si instalatii pentru irigatii;  - masini pentru recoltat, treierat, curatat, sortat si tratat seminte, adunat si balotat fan si paie;  - masini si echipamente pentru lucrarea si cultivarea pamantului, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.1.2.1.",
        "denumire_active_fixe": "- grape, netezitoare si nivelatoare;",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.2.",
        "denumire_active_fixe": "Masini, instalatii si utilaje pentru zootehnie.  Masini, instalatii si utilaje pentru prepararea hranei animalelor.  Masini, instalatii si utilaje pentru adapatul, distribuirea hranei animalelor si evacuarea gunoiului.  Masini, instalatii si utilaje pentru recoltarea produselor animale.  Masini, instalatii si utilaje pentru apicultura.  Masini, instalatii si utilaje pentru incubatii si pentru avicultura.  Masini, instalatii si utilaje pentru dezinfectie veterinara.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.3.",
        "denumire_active_fixe": "Masini, instalatii si utilaje pentru legumicultura, viticultura si pomicultura.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.4.",
        "denumire_active_fixe": "Masini, instalatii si utilaje pentru producerea biogazului.",
        "durata_amortizare_in_ani": "12-20",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.5.",
        "denumire_active_fixe": "Unelte, dispozitive si instrumente folosite in agricultura.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.21.6.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.21.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.1.1.",
        "denumire_active_fixe": "- masini, utilaje si instalatii pentru mentenanta liniilor, locomotivelor si vagoanelor;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.1.2.",
        "denumire_active_fixe": "- instalatii speciale pentru siguranta circulatiei si marirea capacitatii de exploatare in statii, triaje si linii curente CF (instalatii pentru controlul pozitiei macazurilor, instalatii de comanda centralizata a circulatiei, de semnalizare automata a liniilor);  - instalatii de telecomunicatii pentru cai ferate.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.1.3.",
        "denumire_active_fixe": "- masini, utilaje si instalatii folosite in sistemul comercial;  - utilaje pentru impregnarea si ignifugarea lemnului.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru mentenanta mijloacelor de transport rutier.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.3.1.",
        "denumire_active_fixe": "- barci pentru scafandri, din metal;",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.3.2.",
        "denumire_active_fixe": "- pompe de aer pentru scafandri;",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.3.3.",
        "denumire_active_fixe": "- pontoane maritime si fluviale;  - docuri plutitoare; docuri uscate;",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.3.4.",
        "denumire_active_fixe": "- masini, utilaje si instalatii pentru intretinerea cailor navigabile si a lacurilor;  - instalatii pentru intretinerea si repararea navelor.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.3.5.",
        "denumire_active_fixe": "- uzine electrice plutitoare; nave pentru stins incendii; dormitoare plutitoare pe nave sau pe bacuri fluviale.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru exploatarea, mentenanta, protectia si servirea aeronavelor si a traficului aerian.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru posta, presa si telecomunicatii (telefonie, telegrafie), in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.5.1.",
        "denumire_active_fixe": "- centrale automate (telefonice si telegrafice), analogice de oficiu;",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.5.2.",
        "denumire_active_fixe": "- centrale automate(telefonice si telegrafice) analogice pentru institutii.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.5.3.",
        "denumire_active_fixe": "- echipamente digitale de telecomunicatii si instalatii aferente (electroalimentare, climatizare).",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.6.",
        "denumire_active_fixe": "Masini, aparate si instalatii pentru radio, televiziune si telecomunicatii prin sateliti, telefonie mobila, in afara de:",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.6.1.",
        "denumire_active_fixe": "- statii de emisie, emitatoare, translatoare si excitatoare, radiorelee;  - antene;",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.6.2.",
        "denumire_active_fixe": "- statii radio, radiotelefoane mobile, rame de radiorelee mobile;  - receptoare profesionale de trafic de banda larga;  - echipamente pentru telecomunicatii prin sateliti;",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.6.3.",
        "denumire_active_fixe": "- transformatoare de fider pentru monitoare de control video si audio;  - monitoare de control video si audio;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.6.4.",
        "denumire_active_fixe": "- receptoare telefonie mobila.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.7.",
        "denumire_active_fixe": "Echipamente, utilaje si aparate pentru studiouri de radio si televiziune, in afara de:",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.7.1.",
        "denumire_active_fixe": "- echipamente auxiliare pentru controlul si monitorizarea semnalelor.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.8.",
        "denumire_active_fixe": "Unelte, dispozitive si instrumente pentru transporturi si telecomunicatii.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.22.9.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.22.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.1.",
        "denumire_active_fixe": "Masini pentru pregatirea alimentelor.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.2.",
        "denumire_active_fixe": "Masini de spalat vesela si tacamuri.  Dulapuri pentru uscat si incalzit vesela si tacamuri.  Masini, utilaje si instalatii pentru conservarea si desfacerea preparatelor alimentare si a bauturilor.  Linii de autoservire pentru alimentatia publica.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.3.",
        "denumire_active_fixe": "Masini si utilaje pentru prepararea mancarurilor, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.3.1.",
        "denumire_active_fixe": "- marmite.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.4.",
        "denumire_active_fixe": "Automate si semiautomate comerciale. Jocuri de noroc mecanice, electrice, electronice, mese de biliard, etc.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.5.",
        "denumire_active_fixe": "Unelte, dispozitive, instrumente pentru circulatia marfurilor, conteinere si transconteinere.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.23.6",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.23.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.1.",
        "denumire_active_fixe": "Masini pentru spalatorii si curatatorii chimice.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii de salubritate si ingrijirea spatiilor verzi.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.3.",
        "denumire_active_fixe": "Masini, echipamente si instalatii pentru stins incendii, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.3.1.",
        "denumire_active_fixe": "- centrale de avertizare si semnalizare.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.4.",
        "denumire_active_fixe": "Utilaje si instalatii pentru alimentarea cu apa, pentru tratarea apelor de alimentare si epurarea apelor uzate, in afara de:",
        "durata_amortizare_in_ani": "19-29",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.4.1.",
        "denumire_active_fixe": "- aparate de clorinare.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.4.2.",
        "denumire_active_fixe": "- poduri racloare.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.5.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru tratarea deseurilor menajere.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.6.",
        "denumire_active_fixe": "Recipiente pentru depozitarea deseurilor menajere, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.6.1.",
        "denumire_active_fixe": "- rampe ecologice.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.24.7.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.24.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.25.1.",
        "denumire_active_fixe": "Aparate si instrumente pentru oftalmologie, pentru oto-rino- laringologie.  Aparate si instrumente pentru stomatologie.  Aparate si instalatii pentru fizioterapie.  Aparate si instalatii de laborator pentru analize medicale.  Utilaje, instalatii si aparate pentru ocrotire sanatatii (sterilizare, dezinfectii, dezinsectii)",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.25.2.",
        "denumire_active_fixe": "Aparate si instrumente pentru diagnostic, pentru chirurgie, pentru narcoza si reanimare, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.25.2.1.",
        "denumire_active_fixe": "- aparate de inalta tehnologie;  - aparate pentru masurarea presiunii arteriale.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.25.3.",
        "denumire_active_fixe": "Aparate, instrumente, utilaje si instalatii pentru radiologie.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.25.4.",
        "denumire_active_fixe": "Alte masini, utilaje si instalatii neregasite in cadrul clasei 2.1.25.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.1.",
        "denumire_active_fixe": "Masini, aparate si instalatii pentru producerea de filme si proiectie cinematografica, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.1.1.",
        "denumire_active_fixe": "- lampi fulger electronice, proiectoare si cutii de distributie.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.2.",
        "denumire_active_fixe": "Masini, utilaje si instalatii fotografice; utilaje pentru scene de teatru, cluburi si cinematografe, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.2.1.",
        "denumire_active_fixe": "- cortine, scene;",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.2.2.",
        "denumire_active_fixe": "- scene metalice demontabile.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.3.",
        "denumire_active_fixe": "Instrumente muzicale si automate muzicale, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.3.1.",
        "denumire_active_fixe": "- orga clasica cu comanda electrica.",
        "durata_amortizare_in_ani": "40-60",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.4.",
        "denumire_active_fixe": "Masini, utilaje si instalatii pentru producerea de discuri fonografice.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.5.",
        "denumire_active_fixe": "Masini si utilaje pentru hidrometrie. Masini si echipamente pentru saloane de frizerie, coafura si cosmetica, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.26.5.1",
        "denumire_active_fixe": "- unelte si instrumente de frizerie, cosmetica si coafura.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.27.",
        "denumire_active_fixe": "Accesorii de productie.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.1. ECHIPAMENTE TEHNOLOGICE (MASINI, UTILAJE SI INSTALATII DE LUCRU)",
        "cod_clasificare": "2.1.28.",
        "denumire_active_fixe": "Alte echipamente tehnologice (masini, utilaje si instalatii de lucru) neregasite in cadrul subgrupei 2.1.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.1.1.",
        "denumire_active_fixe": "Aparate, instrumente si instalatii pentru masurarea marimilor geometrice.  Aparate si instalatii pentru masurarea marimilor mecanice si acustice, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.1.1.1.",
        "denumire_active_fixe": "- bascule romane pod pentru autovehicule si vagoane.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.1.1.2.",
        "denumire_active_fixe": "- aparate de cantarit si marcat.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.1.1.3.",
        "denumire_active_fixe": "- dozatoare, debitmetre, contoare pentru lichide si gaze.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.1.2.",
        "denumire_active_fixe": "Alte aparate si instalatii pentru masurarea marimilor geometrice, mecanice si acustice neregasite in cadrul clasei 2.2.1.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.2.1.",
        "denumire_active_fixe": "Aparate si instalatii etalon mecanice si electromecanice pentru masurarea timpului; cronografe si calculografe; ceasornice de semnalizare; instalatii pentru verificarea cronometrelor; etaloane de frecventa.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.2.2.",
        "denumire_active_fixe": "Punti de masurat, comparatoare si analizoare de frecventa; instalatii pentru verificarea frecventmetrelor si aparate de masurat deviatia de frecventa, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.2.2.1.",
        "denumire_active_fixe": "- aparate portabile.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.2.3.",
        "denumire_active_fixe": "Alte aparate si instalatii pentru masurarea timpului, frecventei si marimilor cinematice neregasite in cadrul clasei 2.2.2.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.3.1.",
        "denumire_active_fixe": "Elemente Waston; aparate portabile.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.3.2.",
        "denumire_active_fixe": "Alte aparate si instalatii pentru masurarea marimilor electrice, electromagnetice si radiometrice neregasite in cadrul clasei 2.2.3.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.4.1.",
        "denumire_active_fixe": "Termometre de sticla si de cuart; bimetalice si manometrice; termometre cu rezistenta si termocupluri.  Lampi etalon de temperatura, de culoare si luxmetre.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.4.2.",
        "denumire_active_fixe": "Contoare pentru apa calda si energie termica.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.4.3.",
        "denumire_active_fixe": "Alte aparate si instalatii pentru masurarea marimilor termice si fotometrice neregasite in cadrul clasei 2.2.4.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.5.1.",
        "denumire_active_fixe": "Prese hidraulice, platforme seismice pentru incercari, echipamente pentru incercari electrice de mare putere si inalta tensiune.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.5.2.",
        "denumire_active_fixe": "Alte aparate si instalatii pentru masurarea marimilor analitice (de materiale, de structura si de compozitie); aparate si instalatii pentru incercarea materialelor, elementelor si a produselor neregasite in cadrul clasei 2.2.5.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.6.1.",
        "denumire_active_fixe": "Utilaje si accesorii de laborator executate din sticla.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.6.2.",
        "denumire_active_fixe": "Alte utilaje si accesorii de laborator neregasite in cadrul clasei 2.2.6.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.7.",
        "denumire_active_fixe": "Aparate si instalatii pentru cercetare stiintifica.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.8.",
        "denumire_active_fixe": "Instalatii pentru comanda si reglarea automata a proceselor tehnologice, pentru semnalizare si telemasurare.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.9.",
        "denumire_active_fixe": "Calculatoare electronice si echipamente periferice. Masini si aparate de casa, control si facturat.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  -  2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.",
        "cod_clasificare": "2.2.10.",
        "denumire_active_fixe": "Alte aparate si instalatii de masurare, control si reglare neregasite in cadrul subgrupei 2.2.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.1.1.",
        "denumire_active_fixe": "Locomotive, locotractoare si automotoare de ecartament normal.  Vagoane de marfa si de calatori, de ecartament normal.  Locomotive, locotractoare si automotoare de ecartament ingust sau larg.  Vagoane de marfa si de calatori, de ecartament ingust.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.1.2.",
        "denumire_active_fixe": "Locomotive si locotractoare pentru transport minier.  Vagonete de ecartament ingust, pentru transport minier subteran.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.1.3.",
        "denumire_active_fixe": "Patruciclete si triciclete pe linie si vagonete de ecartament normal sau ingust.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.1.4.",
        "denumire_active_fixe": "Alte mijloace de transport feroviar neregasite in cadrul clasei 2.3.1.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.1.",
        "denumire_active_fixe": "- autoturisme, in afara de:",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.1.1.",
        "denumire_active_fixe": "- taxiuri;",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.2.",
        "denumire_active_fixe": "- microbuze;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.3.",
        "denumire_active_fixe": "- autobuze, in afara de:",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.3.1.",
        "denumire_active_fixe": "- autobuze pentru transportul urban;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.1.4.",
        "denumire_active_fixe": "- motociclete si biciclete.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.1.",
        "denumire_active_fixe": "- autocamioane si autocamionete cu platforma fixa, autofurgonete, autofurgoane si autodube de capacitate pana la 4,5 t exclusiv.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.2.",
        "denumire_active_fixe": "- autocamioane, autodube si autofurgoane cu platforma fixa, cu capacitatea de si peste 4,5 t;",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.3.",
        "denumire_active_fixe": "- autocamioane cu platforma basculanta si dumpere;  - autocisterne;  - autoizoterme si autofrigorifere.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.4.",
        "denumire_active_fixe": "- autotractoare si autotractoare cu sa.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.5.",
        "denumire_active_fixe": "- tractoare pe roti si pe senile.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.6.",
        "denumire_active_fixe": "- remorci cu platforma fixa sau basculanta si remorci monoaxe.  - remorci: cisterne, izoterme si frigorifice, semiremorci auto: platforma, furgon, cisterne, izoterme si frigorifice; port transcontainere.  - remorci si semiremorci auto cu destinatie specifica.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.7.",
        "denumire_active_fixe": "- remorci cu platforma coborata pentru sarcini grele (trailere).",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.8.",
        "denumire_active_fixe": "- motociclete si triciclete pentru transportul de marfuri.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.9.1.",
        "denumire_active_fixe": "- autoturnuri, autotelescoape, autoateliere si autodepanatoare,",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.9.2.",
        "denumire_active_fixe": "- autovehicule pentru transportul materialelor pulverulente;  - autovehicule cu troliu pentru busteni.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.2.9.3.",
        "denumire_active_fixe": "- alte autovehicule cu destinatie speciala",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.2.3.",
        "denumire_active_fixe": "Alte mijloace de transport auto neregasite in cadrul clasei 2.3.2.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.1.",
        "denumire_active_fixe": "Nave maritime de calatori, de cursa lunga si costiere.  Nave maritime mixte de calatori si marfuri.  Nave maritime pentru marfuri de masa in vrac (mineraliere) si pentru produse petroliere (petroliere).  Remorchere maritime de linie pentru transport.  Nave maritime tehnice si speciale.  Remorchere maritime portuare.  Nave maritime depozit; tancuri: de buncheraj, de apa potabile si mixte. Iahturi maritime.  Nave fluviale pentru transport de calatori.  Nave fluviale cu propulsie, pentru transport de marfuri diferite.  Bacuri, mahoane si barcaze fluviale pentru marfuri uscate; ceamuri fluviale cu corp metalic, fara propulsie, pentru stuf.  Bacuri, mahoane si viviere fluviale pentru productie si transportat peste.  Pontoane de leasa, cu doua flotoare metalice si platforma din lemn.  Nave fluviale de trecere (bacuri de trecere fluviale, cu sau fara propulsie, pentru vehicule si calatori; poduri plutitoare fluviale, pe cablu).  Nave fluviale tehnice si speciale; auxiliare si de servitute.  Nave fluviale, iahturi si salupe de agrement.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.2.",
        "denumire_active_fixe": "Mahoane maritime, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.2.1.",
        "denumire_active_fixe": "- din lemn.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.3.",
        "denumire_active_fixe": "Nave maritime de pescuit, in afara de:",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.3.1.",
        "denumire_active_fixe": "- pescadoare cu corp din lemn.",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.3.2.",
        "denumire_active_fixe": "- pescadoare cu corp metalic. - cutere cu corp din lemn, pentru productie si transportat peste.",
        "durata_amortizare_in_ani": "14-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.4.",
        "denumire_active_fixe": "Doc plutitor.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.5.",
        "denumire_active_fixe": "Salupe maritime pentru calatori.  Salupe maritime.  Nave fluviale fara propulsie pentru transport de marfuri diferite",
        "durata_amortizare_in_ani": "14-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.6.",
        "denumire_active_fixe": "Pilotine maritime.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.7.1.",
        "denumire_active_fixe": "- cu corp din lemn.",
        "durata_amortizare_in_ani": "L 9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.7.2.",
        "denumire_active_fixe": "- cu corp din metal.",
        "durata_amortizare_in_ani": "14-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.8.",
        "denumire_active_fixe": "Ambarcatii fluviale de agrement (barci de agrement, canoe de agrement, giguri, sandoline si hidrobiciclete).  Ambarcatii fluviale si de pescuit (mahoane de taliene, barci viviere, barci de furajat, pramuri si navodnice).",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.9.",
        "denumire_active_fixe": "Ambarcatii fluviale auxiliare de deservire generala si sportive, in afara de:",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.9.1.",
        "denumire_active_fixe": "- cu corp metalic.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.10.",
        "denumire_active_fixe": "Barci pescaresti.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.3.11.",
        "denumire_active_fixe": "Alte mijloace de transport naval neregasite in cadrul clasei 2.3.3.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.4.1.",
        "denumire_active_fixe": "Avioane pentru transport de calatori, marfuri si mixte.",
        "durata_amortizare_in_ani": "14-22",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.4.2.",
        "denumire_active_fixe": "Avioane pentru destinatie speciala: imprastierea ingrasamintelor chimice, insectofungicidelor la lucrari agrosilvice, sanitare.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.4.3.",
        "denumire_active_fixe": "Elicoptere pentru transport de calatori, marfuri sau destinatie speciala (imprastierea ingrasamintelor, montaj, etc.).",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.4.4.",
        "denumire_active_fixe": "Alte mijloace de transport aerian neregasite in cadrul clasei 2.3.4.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.5.1.",
        "denumire_active_fixe": "Mijloace de transport electric urban pe sine.",
        "durata_amortizare_in_ani": "11-17",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.5.2.",
        "denumire_active_fixe": "Mijloace de transport electric urban, pe pneuri (troleibuze).",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.5.3.",
        "denumire_active_fixe": "Alte mijloace specifice pentru transportul urban de calatori neregasite in cadrul clasei 2.3.5.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.1.",
        "denumire_active_fixe": "Mecanisme de ridicat (vinciuri, trolii etc.).  Macarale diverse si speciale, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.1.1.",
        "denumire_active_fixe": "- macarale plutitoare.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.1.2.",
        "denumire_active_fixe": "- macarale feroviare si macarale transcontainer.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.2.",
        "denumire_active_fixe": "Macarale rotitoare; macarale rulante cu platforma si poduri rulante, in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.2.1.",
        "denumire_active_fixe": "- macarale rotitoare stationare, fixe, cu coloana, macarale turn cu actionare electrica.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.2.2.",
        "denumire_active_fixe": "- macarale mobile pe pneuri si senile, automacarale.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.3:1.",
        "denumire_active_fixe": "- de materiale si persoane pentru lucrari de constructii; de marfuri.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.3.2.",
        "denumire_active_fixe": "- de persoane pentru cladiri.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.3.3.",
        "denumire_active_fixe": "- de materiale si persoane pentru lucrari miniere",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.4.",
        "denumire_active_fixe": "Transportoare si instalatii de transport pneumatic, in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.4.1.",
        "denumire_active_fixe": "- transportoare cu banda si placi; cu lant (cablu), cu ghiare, cu role, suspendate si cu lanturi de tractiune, portante; transportare cu cupe si sisteme de transportoare utilizate in industrie pentru operatii de prelucrare, asamblare si montaj.",
        "durata_amortizare_in_ani": "7-11",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.4.2.",
        "denumire_active_fixe": "- transportoare cu banda mobile.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.4.3.",
        "denumire_active_fixe": "- transportoare elicoidale si cu raclete.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.4.4.",
        "denumire_active_fixe": "- jgheaburi si topogane; instalatii de transport hidraulic.",
        "durata_amortizare_in_ani": "8-14",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.5.",
        "denumire_active_fixe": "Elevatoare, escalatoare si alimentatoare.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.6.",
        "denumire_active_fixe": "Incarcatoare, impingatoare si basculatoare, in afara de:",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.6.1.",
        "denumire_active_fixe": "- incarcatoare frontale cu o cupa.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.7.",
        "denumire_active_fixe": "Placi turnante pentru intoarcerea locomotivelor.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.8.",
        "denumire_active_fixe": "Alte utilaje, instalatii si echipamente de transportat si de ridicat, neregasite in cadrul clasei 2.3.6., in afara de:",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.6.8.1.",
        "denumire_active_fixe": "- electro si motostivuitoare.",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.3. MIJLOACE DE TRANSPORT",
        "cod_clasificare": "2.3.7.",
        "denumire_active_fixe": "Mijloace de transport cu tractiune animala.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.1.",
        "denumire_active_fixe": "Cai de reproducere si de munca. Magari si catari.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.2.",
        "denumire_active_fixe": "Boi si bivoli de munca; vaci de lapte si tauri pentru reproducere.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.3.",
        "denumire_active_fixe": "Oi, capre si porci pentru reproducere.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.4.",
        "denumire_active_fixe": "Pasari de reproducere.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.5.",
        "denumire_active_fixe": "Caini de paza si vanatoare",
        "durata_amortizare_in_ani": "4-8",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.1.6.",
        "denumire_active_fixe": "Alte animale necuprinse in cadrul clasei 2.4.1.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.1.",
        "denumire_active_fixe": "Plantatii de meri, peri, pruni, gutui, duzi, migdali, castani",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.2.",
        "denumire_active_fixe": "Plantatii de ciresi, visini, piersici, aluni si caisi",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.3",
        "denumire_active_fixe": "Plantatii de nuci",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.4.",
        "denumire_active_fixe": "Plantatii de agrisi, coacazi si trandafiri de dulceata",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.5.",
        "denumire_active_fixe": "Plantatii de zmeura si alti arbusti si subarbusti (muri, capsuni etc.).",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.6.1.",
        "denumire_active_fixe": "- vii altoite (nobile) si portaltoi vie.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.6.2.",
        "denumire_active_fixe": "- vii indigene, vii hibride, producatori directi.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.7.",
        "denumire_active_fixe": "Plantatii de hamei.",
        "durata_amortizare_in_ani": "13-21",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.8.1.",
        "denumire_active_fixe": "- foioase si rasinoase.",
        "durata_amortizare_in_ani": "50-70",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.8.2.",
        "denumire_active_fixe": "- plopi, salcami si salcii.",
        "durata_amortizare_in_ani": "24-36",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.9.",
        "denumire_active_fixe": "Rachitarii.",
        "durata_amortizare_in_ani": "5-9",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.4. ANIMALE SI PLANTATII.",
        "cod_clasificare": "2.4.2.10.",
        "denumire_active_fixe": "Alte plantatii neregasite in cadrul clasei 2.4.2.",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII  - 2.5. ALTE INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII ",
        "cod_clasificare": "2.5.",
        "denumire_active_fixe": "Alte instalatii tehnice, mijloace de transport, animale si plantatii neregasite in cadrul grupei 2.",
        "durata_amortizare_in_ani": "20-30",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.1.",
        "denumire_active_fixe": "Mobilier (inclusiv mobilierul comercial si hotelier), in afara de:",
        "durata_amortizare_in_ani": "9-15",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.1.1.",
        "denumire_active_fixe": "- mobilier comercial de prezentare din lemn si plastic cu structura metalica usoara",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.2.",
        "denumire_active_fixe": "Firme, panouri si reclame luminoase.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.3.",
        "denumire_active_fixe": "Tablouri, gravuri, decoratiuni interioare, in afara celor inregistrate in patrimoniul cultural national.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.4.",
        "denumire_active_fixe": "Inventar gospodaresc: tacamuri din metale pretioase, covoare, oglinzi, candelabre, etc.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.5.",
        "denumire_active_fixe": "Aparate electrocasnice; aparate radio-receptoare, televizoare, aparatura video, masini de spalat rufe, masini de spalat vase, frigidere, aspiratoare de praf, etc.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.1.6.",
        "denumire_active_fixe": "Alt mobilier neregasit in cadrul grupei 3.1.",
        "durata_amortizare_in_ani": "6-10",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.2.1.",
        "denumire_active_fixe": "Masini de scris, de francat, aparate de dictat si reprodus, aparate de desenat, heliografe, aparate de copiat si multiplicat, aparate de proiectie, aparate de citit microfilme etc.",
        "durata_amortizare_in_ani": "4-6",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.2.2.",
        "denumire_active_fixe": "Aparate de telecomunicatii pentru birou: aparate telefonice, aparate telefax, aparate telex, instalatii de comanda prin radio, aparate de cautat persoane etc.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.2.3.",
        "denumire_active_fixe": "Masini de numarat si identificat bani.",
        "durata_amortizare_in_ani": "2-4",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.2.4.",
        "denumire_active_fixe": "Alta aparatura birotica neregasita in cadrul subgrupei 3.2.",
        "durata_amortizare_in_ani": "3-5",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.1.",
        "denumire_active_fixe": "Echipamente de protectie mecanica - grilaje, gratare, usi blindate, usi de securitate, ferestre si panouri de securitate (antiefractie, antivandal, antiglont).",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.2.",
        "denumire_active_fixe": "Unitati de depozitare valori si purtatori de date (case de bani, seifuri, dulapuri ignifuge etc.).",
        "durata_amortizare_in_ani": "16-24",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.3.",
        "denumire_active_fixe": "Automate bancare, bancomate.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.4.",
        "denumire_active_fixe": "Sisteme de protectie la incendiu (elemente de detectie si de actionare, centrale de semnalizare si actionare etc.).",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.5.",
        "denumire_active_fixe": "Sisteme pentru identificare si controlul accesului supraveghere si alarma la efractie.",
        "durata_amortizare_in_ani": "8-12",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.3.6.",
        "denumire_active_fixe": "Alte sisteme de protectie a valorilor umane si materiale neregasite in cadrul subgrupei 3.3.",
        "durata_amortizare_in_ani": "12-18",
    },
    {
        "grupa": "GRUPA 3. MOBILIER, APARATURA BIROTICA, SISTEME DE PROTECTIE A VALORILOR UMANE SI MATERIALE SI ALTE ACTIVE CORPORALE",
        "cod_clasificare": "3.4.",
        "denumire_active_fixe": "Alte active corporale neregasite in cele specificate la grupa 3.",
        "durata_amortizare_in_ani": "8-15",
    },
]
