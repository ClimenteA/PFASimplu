import os
import requests
import requests_cache
from datetime import timedelta
from core.settings import get_current_version, get_extracts_path


cache_path = os.path.join(get_extracts_path(), 'app_version_cache')

requests_cache.install_cache(cache_path, backend='filesystem', expire_after=timedelta(days=1))

def new_version_available():
    try:
        current_version = get_current_version()
        response = requests.get("https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/static/versiune.txt")
        return response.text != current_version
    except Exception as err:
        print("Nu am putut verifica daca a aparut o noua versiune:", err)
        return False
