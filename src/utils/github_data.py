import logging
import os
import tomllib
from datetime import timedelta

import requests_cache

from core.settings import get_extracts_path

cache_path = os.path.join(get_extracts_path(), "app_version_cache")
requests_session = requests_cache.CachedSession(
    cache_path, backend="filesystem", expire_after=timedelta(days=1)
)


PYPROJECT_URL = "https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/pyproject.toml"

logger = logging.getLogger(__name__)


def get_latest_app_version():
    """Ultima versiune publicata, citita din pyproject.toml de pe GitHub
    (campul project.version). Returneaza '' daca nu poate fi preluata.

    refresh=True e important: cache-ul HTTP de o zi ar putea afisa o versiune
    veche, asa ca sursa de adevar e intotdeauna fisierul de pe GitHub.
    """
    try:
        response = requests_session.get(PYPROJECT_URL, timeout=5, refresh=True)
        response.raise_for_status()
        return tomllib.loads(response.text)["project"]["version"]
    except Exception:
        logger.exception("Nu am putut prelua ultima versiune PFASimplu de pe GitHub")
        return ""
