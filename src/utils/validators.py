from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_not_future_date(value):
    if not value: return
    if value > timezone.now().date():
        raise ValidationError(_("Incasarea nu poate fi din viitor."))
