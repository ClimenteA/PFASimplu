import re
import secrets
import string

from django.db import models

from .multiuser import get_user_media_prefix

chars = string.digits + string.ascii_letters


def get_short_id(length: int = 8):
    return "".join(secrets.choice(chars) for _ in range(length))


def get_save_path(instance: models.Model, filename: str):
    # Scoate doar un id anterior de 8 caractere alfanumerice de la inceputul numelui.
    # Vechiul regex r"(.{8}_).*" nu era ancorat si taia orice 8 caractere urmate de "_"
    # oriunde in nume (ex. "2025-05_Factura-002_Wizeline.pdf" -> "2025-05_FacWizeline.pdf").
    filename = re.sub(r"^[A-Za-z0-9]{8}_", "", filename)
    # Fisierele fiecarui utilizator stau in media/user_<id>/.
    prefix = get_user_media_prefix()
    if not prefix and getattr(instance, "user_id", None):
        # Salvare in afara unei cereri (ex. import, shell) cu user explicit.
        prefix = f"user_{instance.user_id}/"
    return prefix + get_short_id(8) + "_" + filename


def media_serve_view(request, path):
    """Serveste fisierele din /media/ doar proprietarului autentificat.

    Fiecare utilizator isi vede doar folderul lui (media/user_<id>/); fisierele
    vechi din radacina media/ sunt servite doar superutilizatorilor.
    """
    from django.conf import settings
    from django.http import Http404
    from django.views.static import serve

    if not request.user.is_authenticated:
        raise Http404()
    prefix = get_user_media_prefix()
    if not path.startswith(prefix) and not request.user.is_superuser:
        # Folderul altui utilizator (sau fisiere fara proprietar).
        raise Http404()

    return serve(request, path, document_root=settings.MEDIA_ROOT)
