"""Initializare Django pentru procesele MCP (stdio / HTTP).

Serverul MCP ruleaza intr-un proces separat fata de aplicatia web (waitress),
dar foloseste aceeasi baza de date si acelasi folder media.
"""

import os
import sys
from pathlib import Path


def setup_django() -> None:
    root = Path(__file__).resolve().parent.parent  # src/
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django

    django.setup()
