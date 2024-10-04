import os
import requests
import requests_cache
from datetime import timedelta
from core.settings import get_current_version, get_extracts_path, get_salarii_minim_brut_local


cache_path = os.path.join(get_extracts_path(), 'app_version_cache')
requests_cache.install_cache(cache_path, backend='filesystem', expire_after=timedelta(days=1))


get_url = lambda filename: f"https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/static/{filename}"


def new_version_available():
    try:
        current_version = get_current_version()
        response = requests.get(get_url("versiune.txt"))
        return response.text != current_version
    except Exception as err:
        print("Nu am putut verifica daca a aparut o noua versiune:", err)
        return False


def get_salarii_minim_brut():
    try:
        response = requests.get(get_url("minim_brut_an_val.json"))
        data = response.json()
        data = {int(k): v for k, v in data.items()}
        return data
    except Exception as err:
        print("Nu am putut prelua ultimele salarii minime brute:", err)
        return get_salarii_minim_brut_local()
