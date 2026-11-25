from django.conf import settings
from django.db import models
from .files import get_save_path
from .multiuser import get_current_user
from .valuta import Valuta, TipTranzactie, to_ron
from .validators import validate_not_future_date
from django.utils import timezone


class UserScopedManager(models.Manager):
    """Manager care izoleaza datele per utilizator in modul multi-user.

    In modul desktop (implicit) se comporta ca managerul standard.
    In modul multi-user filtreaza automat dupa utilizatorul cererii curente;
    fara utilizator in context (admin, shell, comenzi de management) nu
    filtreaza - paginile web cer oricum autentificare prin middleware.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if settings.MULTI_USER:
            user = get_current_user()
            if user is not None and not user.is_superuser:
                return qs.filter(user=user)
        return qs


class UserOwnedModel(models.Model):
    """Baza pentru toate modelele cu date ale utilizatorului.
    `user` ramane null in modul desktop; in modul multi-user se completeaza
    automat la salvare cu utilizatorul autentificat."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
    )

    objects = UserScopedManager()

    def save(self, *args, **kwargs):
        if settings.MULTI_USER and self.user_id is None:
            user = get_current_user()
            if user is not None:
                self.user = user
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class CommonIncasariCheltuieliModel(UserOwnedModel):
    """Faptele introduse de utilizator pentru o incasare sau cheltuiala.

    Valorile in RON NU mai sunt coloane: se calculeaza din `suma`, `valuta` si
    data, folosind cursul BNR pastrat in `utils.CursBnr` (o singura sursa).
    """

    suma = models.DecimalField(max_digits=14, decimal_places=4)
    valuta = models.CharField(max_length=3, choices=Valuta, default=Valuta.RON)
    tip_tranzactie = models.CharField(
        max_length=7, choices=TipTranzactie, default=TipTranzactie.BANCAR
    )
    data_inserarii = models.DateField(
        null=True, blank=True, validators=[validate_not_future_date]
    )
    fisier = models.FileField(max_length=100_000, upload_to=get_save_path)
    actualizat_la = models.DateTimeField(default=timezone.now)

    @property
    def suma_in_ron(self):
        return to_ron(self.suma, self.valuta, self.data_inserarii)

    class Meta:
        abstract = True


# Nume sugerat in designul de schema; pastram si vechiul nume pentru importuri.
TranzactieModel = CommonIncasariCheltuieliModel
