import re
import string
import secrets
from django.db import models


chars = string.digits + string.ascii_letters

def get_short_id(length: int = 8):
    return ''.join(secrets.choice(chars) for _ in range(length))


def get_save_path(instance: models.Model, filename: str):
    # Scoate doar un id anterior de 8 caractere alfanumerice de la inceputul numelui.
    # Vechiul regex r"(.{8}_).*" nu era ancorat si taia orice 8 caractere urmate de "_"
    # oriunde in nume (ex. "2025-05_Factura-002_Wizeline.pdf" -> "2025-05_FacWizeline.pdf").
    filename = re.sub(r"^[A-Za-z0-9]{8}_", "", filename)
    return get_short_id(8) + "_" + filename
