import os
import tomllib
import traceback
import requests_cache
from datetime import timedelta
from core.settings import get_extracts_path, get_salarii_minim_brut_local


cache_path = os.path.join(get_extracts_path(), 'app_version_cache')
requests_session = requests_cache.CachedSession(cache_path, backend='filesystem', expire_after=timedelta(days=1))


get_url = lambda filename: f"https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/static/{filename}"


def get_latest_app_version():
    """Ultima versiune publicata, citita din pyproject.toml de pe GitHub
    (campul project.version). Returneaza '' daca nu poate fi preluata."""
    try:
        response = requests_session.get(
            "https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/pyproject.toml",
            timeout=5,
        )
        response.raise_for_status()
        return tomllib.loads(response.text)["project"]["version"]
    except Exception as err:
        print(traceback.format_exc())
        print("Nu am putut prelua ultima versiune PFASimplu de pe GitHub:", str(err))
        return ""


def get_salarii_minim_brut():
    try:
        response = requests_session.get(get_url("minim_brut_an_val.json"))
        data = response.json()
        data = {int(k): v for k, v in data.items()}
        return data
    except Exception as err:
        print(traceback.format_exc())
        print("Nu am putut prelua ultimele salarii minime brute:", str(err))
        return get_salarii_minim_brut_local()
