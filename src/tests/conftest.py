"""Infrastructura testelor end-to-end (Playwright + Faker).

Testele ruleaza impotriva unui server Django pornit pe o baza de date SQLite
separata (`src/tests/.runtime/test.db`), ca sa nu atinga datele reale din
`src/dbsqlite/stocare.db`. Migrarile sunt generate automat la fiecare rulare
(proiectul nu tine migrarile in git - vezi `make purge-migration-dirs`).

Rulare:
    uv run pytest src/tests/ -v                 # headless
    uv run pytest src/tests/ -v --headed        # cu browser vizibil
    uv run pytest src/tests/ -v --slowmo 300    # incetinit, pentru urmarire

Dupa rulare, baza de date de test ramane in src/tests/.runtime/ si poate fi
inspectata (sau incarcata in aplicatie) pentru verificari manuale.
"""

import datetime
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from faker import Faker

SRC_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = Path(__file__).resolve().parent / ".runtime"
FILES_DIR = RUNTIME_DIR / "files"

# pytest pune in sys.path doar directorul tests/, asa ca adaugam src/ pentru
# a importa app-urile Django din procesul de test.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Testele folosesc si ORM-ul Django (pentru valorile calculate ca proprietati),
# deci procesul de pytest trebuie sa vada aceeasi baza ca serverul de test.
os.environ.setdefault("PFASIMPLU_DB_PATH", str(RUNTIME_DIR / "test.db"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
# pytest-playwright ruleaza testele intr-un context cu event loop, iar ORM-ul
# e folosit doar pentru verificari sincrone pe baza de date de test.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

# Anul acoperit de teste: anul curent. Aplicatia nu accepta date din viitor
# (validate_not_future_date), deci lunile viitoare sunt sarite automat.
TEST_YEAR = datetime.date.today().year
TODAY = datetime.date.today()
LAST_MONTH = TODAY.month if TEST_YEAR == TODAY.year else 12

# Venitul total anual trebuie sa ramana sub plafonul de 395.000 RON.
VENIT_MAX_RON = 395_000

fake = Faker("ro_RO")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: teste end-to-end pe un an intreg")


@pytest.fixture(scope="session")
def django_server():
    """Porneste `manage.py runserver` pe o baza de date izolata de teste."""
    RUNTIME_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    db_path = RUNTIME_DIR / "test.db"
    if db_path.exists():
        db_path.unlink()

    env = os.environ.copy()
    env["PFASIMPLU_DB_PATH"] = str(db_path)
    env["DJANGO_SETTINGS_MODULE"] = "core.settings"

    manage = [sys.executable, str(SRC_DIR / "manage.py")]

    # Proiectul nu versioneza migrarile: le generam la fiecare rulare.
    # `makemigrations` fara argumente NU detecteaza app-urile fara folder
    # migrations/, de aceea le enumeram explicit (ca in Makefile).
    apps_fara_migratii = [
        app
        for app in ("utils", "cheltuieli", "documente", "facturi", "incasari", "setari")
        if not (SRC_DIR / app / "migrations").exists()
    ]
    cmds = []
    if apps_fara_migratii:
        cmds.append(["makemigrations", *apps_fara_migratii])
    cmds.append(["migrate", "--noinput"])
    for cmd in cmds:
        result = subprocess.run(
            manage + cmd, cwd=SRC_DIR, env=env, capture_output=True, text=True
        )
        assert result.returncode == 0, f"{cmd} a esuat:\n{result.stdout}\n{result.stderr}"

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    server_log = open(RUNTIME_DIR / "server.log", "w")
    server = subprocess.Popen(
        manage + ["runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=SRC_DIR,
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"

    deadline = time.time() + 60
    while time.time() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Serverul Django s-a oprit neasteptat la pornire.")
        try:
            with urllib.request.urlopen(base_url + "/setari/", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.3)
    else:
        server.terminate()
        server_log.close()
        raise RuntimeError(
            "Serverul Django nu a pornit in 60 de secunde. "
            f"Vezi {RUNTIME_DIR / 'server.log'}"
        )

    yield {"base_url": base_url, "db_path": db_path}

    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
    server_log.close()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "slow_mo": int(os.environ.get("SLOWMO", 0))}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, django_server):
    return {
        **browser_context_args,
        "base_url": django_server["base_url"],
        "viewport": {"width": 1600, "height": 1000},
    }


@pytest.fixture(scope="session")
def db(django_server):
    """Acces direct (sqlite3) la baza de date de test, pentru verificari."""
    import sqlite3

    conn = sqlite3.connect(django_server["db_path"])
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def faker_ro():
    return fake


def luna_zi(year: int, month: int, max_day: int | None = None) -> datetime.date:
    """O zi din luna data, fara a depasi ziua curenta (aplicatia respinge
    datele din viitor pentru incasari/cheltuieli)."""
    import calendar

    last_day = calendar.monthrange(year, month)[1]
    if year == TODAY.year and month == TODAY.month:
        last_day = min(last_day, TODAY.day)
    if max_day:
        last_day = min(last_day, max_day)
    return datetime.date(year, month, fake.random_int(min=1, max=last_day))
