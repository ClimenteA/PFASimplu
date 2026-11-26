"""Launcher pentru executabilul standalone PFASimplu.

Alege un director de date in care utilizatorul are drept de scriere, seteaza
variabilele PFASIMPLU_* inainte de incarcarea setarilor Django si porneste
aplicatia intr-o fereastra de tip desktop (flaskwebgui), doar pe 127.0.0.1.
"""

import logging
import os
import secrets
import sys
import webbrowser
from pathlib import Path

APP_NAME = "PFASimplu"
DEFAULT_PORT = 8990

log = logging.getLogger("pfasimplu.launcher")


def default_data_dir() -> Path:
    """Directorul de date al utilizatorului, in functie de sistemul de operare."""
    override = os.environ.get("PFASIMPLU_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Local" / APP_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "pfasimplu"


def _read_or_create_secret(path: Path) -> str:
    """Cheia secreta se genereaza o singura data si ramane langa date."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        pass

    secret = secrets.token_urlsafe(48)
    try:
        # 0o600 din creare, ca sa nu existe o fereastra cu permisiuni largi.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path.read_text(encoding="utf-8").strip()
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(secret)
    return secret


def prepare_environment(data_dir: Path) -> dict[str, Path]:
    """Creeaza folderele si seteaza mediul inainte de importul setarilor Django."""
    paths = {
        "db": data_dir / "db",
        "files": data_dir / "files",
        "logs": data_dir / "logs",
        "static": data_dir / "staticfiles",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    secret = _read_or_create_secret(data_dir / "secret_key")

    env = {
        "PFASIMPLU_DB_DIR": paths["db"],
        "PFASIMPLU_MEDIA_ROOT": paths["files"],
        "PFASIMPLU_LOG_DIR": paths["logs"],
        "PFASIMPLU_STATIC_ROOT": paths["static"],
        "PFASIMPLU_SECRET_KEY": secret,
        "PFASIMPLU_DEBUG": "0",
        "PFASIMPLU_ALLOWED_HOSTS": "127.0.0.1,localhost",
        "PFASIMPLU_SECURE_COOKIES": "0",
    }
    for key, value in env.items():
        os.environ.setdefault(key, str(value))
    return paths


def _create_server(application, start_port: int):
    import waitress

    for port in range(start_port, start_port + 100):
        try:
            return waitress.create_server(
                application, host="127.0.0.1", port=port, threads=8
            )
        except OSError:
            continue
    raise RuntimeError(
        f"Niciun port liber in intervalul {start_port}-{start_port + 99}"
    )


def main() -> None:
    log.setLevel(logging.INFO)
    if not log.handlers:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(console)

    data_dir = default_data_dir()
    paths = prepare_environment(data_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    os.environ.setdefault("FLASKWEBGUI_LOG_LEVEL", "WARNING")

    import django

    django.setup()

    from django.core.management import call_command

    # Migrarile si fisierele statice sunt idempotente; ruleaza la fiecare
    # pornire ca un upgrade de executabil sa se aplice singur.
    call_command("migrate", interactive=False, verbosity=0)
    call_command("collectstatic", interactive=False, verbosity=0)

    from core.wsgi import application

    start_port = int(os.environ.get("PFASIMPLU_PORT", DEFAULT_PORT))
    server = _create_server(application, start_port)
    port = server.effective_port
    url = f"http://127.0.0.1:{port}"

    log.info("Date PFASimplu: %s", data_dir)
    log.info("Loguri: %s", paths["logs"])
    log.info("PFASimplu ruleaza la %s (Ctrl+C pentru oprire)", url)

    if os.environ.get("PFASIMPLU_NO_BROWSER") == "1":
        try:
            server.run()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
        return

    try:
        from flaskwebgui import FlaskUI
    except ImportError:
        log.warning("flaskwebgui lipseste; deschid browserul implicit.")
        webbrowser.open(url)
        try:
            server.run()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
        return

    logging.getLogger("flaskwebgui").setLevel(logging.WARNING)

    def run_server(**_kwargs):
        server.run()

    ui = FlaskUI(
        server=run_server,
        server_kwargs={"app": application, "port": port},
        width=1280,
        height=860,
        on_shutdown=server.close,
    )
    if ui.browser_path is None:
        # Fara Chrome/Edge/Chromium, flaskwebgui nu are ce fereastra sa
        # deschida; folosim browserul implicit si inchidem cu Ctrl+C.
        log.warning(
            "Nu am gasit Chrome/Edge/Chromium; folosesc browserul implicit. "
            "Inchiderea aplicatiei se face cu Ctrl+C."
        )
        ui.browser_command = [
            sys.executable,
            "-c",
            "import sys, webbrowser; webbrowser.open(sys.argv[1])",
            url,
        ]

    server_process = None
    try:
        server_process, _browser_thread = ui.run()
    finally:
        import flaskwebgui

        browser = flaskwebgui.FLASKWEBGUI_BROWSER_PROCESS
        if browser is not None and browser.poll() is None:
            # Ctrl+C: oprim browserul fara ca flaskwebgui sa mai omoare portul.
            ui.auto_close = False
            browser.terminate()
        # Pe macOS flaskwebgui ruleaza serverul intr-un Process, nu Thread.
        if (
            server_process is not None
            and hasattr(server_process, "terminate")
            and server_process.is_alive()
        ):
            server_process.terminate()
        server.close()


if __name__ == "__main__":
    main()
