import string
import secrets
from django.db import models


chars = string.digits + string.ascii_letters

def get_short_id(length: int = 8):
    return ''.join(secrets.choice(chars) for _ in range(length))


def get_save_path(instance: models.Model, filename: str):
    return get_short_id(8) + "_" + filename
