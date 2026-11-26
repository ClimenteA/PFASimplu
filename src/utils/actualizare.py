"""Descarcarea si instalarea executabilului standalone.

Datele utilizatorului stau in directorul de date (PFASIMPLU_DATA_DIR), nu langa
executabil, deci inlocuirea binarului nu le atinge. PyCrucible re-extrage
wheel-ul la fiecare pornire, dar nu sterge fisierele vechi: curatam wheel-urile
si uv.lock-ul din pycrucible_payload dupa swap, altfel runtime-ul gaseste mai
multe wheel-uri si refuza sa porneasca.
"""

import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

from core.settings import GITHUB_REPO_URL

logger = logging.getLogger(__name__)

VERSIUNE_RE = re.compile(r"^\d+\.\d+\.\d+$")
DIMENSIUNE_MAXIMA = 200 * 1024 * 1024
TIMEOUT = (5, 60)


class EroareActualizare(Exception):
    """Eroare care poate fi afisata utilizatorului in pagina Setari."""


def _platforma() -> tuple[str, str]:
    sistem = platform.system().lower()
    os_name = {"darwin": "macos", "windows": "windows", "linux": "linux"}.get(
        sistem, sistem
    )
    masina = platform.machine().lower()
    arhitectura = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(masina, masina)
    return os_name, arhitectura


def nume_asset(versiune: str) -> str:
    """Numele fisierului din release, identic cu cel din scripts/build_dist.py."""
    if not VERSIUNE_RE.fullmatch(versiune):
        raise EroareActualizare("Versiunea publicata nu are un format cunoscut.")
    os_name, arhitectura = _platforma()
    sufix = ".exe" if os_name == "windows" else ""
    return f"pfasimplu-{versiune}-{os_name}-{arhitectura}{sufix}"


def url_actualizare(versiune: str) -> str:
    return f"{GITHUB_REPO_URL}/releases/download/v{versiune}/{nume_asset(versiune)}.zip"


def _director_payload() -> Path | None:
    """PyCrucible ruleaza python-ul din <exe_dir>/pycrucible_payload/.venv."""
    for parinte in Path(sys.executable).resolve().parents:
        if parinte.name == "pycrucible_payload":
            return parinte
    return None


def calea_executabilului() -> Path | None:
    """Calea binarului curent, sau None in Docker/dev (nu se poate inlocui)."""
    payload = _director_payload()
    if payload is None:
        return None
    nume = os.environ.get("PFASIMPLU_EXE_NAME")
    if nume:
        executabil = payload.parent / nume
        if executabil.is_file():
            return executabil
    # Fallback pentru binare vechi (fara marker) sau pentru executabilul
    # pastrat sub numele versiunii anterioare dupa o actualizare.
    for candidat in payload.parent.glob("pfasimplu-*"):
        if candidat.is_file() and candidat.suffix.lower() in ("", ".exe"):
            return candidat
    return None


def este_standalone() -> bool:
    return calea_executabilului() is not None


def descarca_executabil(versiune: str, director: Path) -> Path:
    """Descarca arhiva release-ului si extrage numai executabilul asteptat."""
    nume = nume_asset(versiune)
    url = url_actualizare(versiune)
    arhiva = director / "actualizare.zip"
    logger.info("Descarc actualizarea %s de la %s", versiune, url)

    try:
        with requests.get(url, stream=True, timeout=TIMEOUT) as raspuns:
            raspuns.raise_for_status()
            total = 0
            with arhiva.open("wb") as iesire:
                for bucata in raspuns.iter_content(chunk_size=1 << 16):
                    if not bucata:
                        continue
                    total += len(bucata)
                    if total > DIMENSIUNE_MAXIMA:
                        raise EroareActualizare("Arhiva de actualizare este prea mare.")
                    iesire.write(bucata)

        with zipfile.ZipFile(arhiva) as continut:
            membru = next(
                (info for info in continut.infolist() if info.filename == nume), None
            )
            if membru is None or membru.is_dir():
                raise EroareActualizare(
                    "Arhiva nu contine executabilul asteptat pentru acest sistem."
                )
            if membru.file_size > DIMENSIUNE_MAXIMA:
                raise EroareActualizare("Executabilul din arhiva este prea mare.")
            executabil = director / nume
            with continut.open(membru) as sursa, executabil.open("wb") as iesire:
                shutil.copyfileobj(sursa, iesire)
    except EroareActualizare:
        raise
    except (requests.RequestException, OSError, zipfile.BadZipFile) as exc:
        logger.warning("Nu am putut descarca actualizarea: %s", exc)
        raise EroareActualizare(
            "Nu am putut descarca actualizarea. Verifica conexiunea la internet "
            "si incearca din nou."
        ) from exc
    finally:
        arhiva.unlink(missing_ok=True)

    if not executabil.is_file() or executabil.stat().st_size == 0:
        raise EroareActualizare("Executabilul descarcat este gol.")
    return executabil


def _script_windows(executabil: Path, nou: Path, payload: Path) -> str:
    return f"""@echo off
rem Inlocuirea se face dupa ce aplicatia si-a eliberat executabilul.
:wait
tasklist /FI "IMAGENAME eq {executabil.name}" 2>NUL | find /I /N "{executabil.name}" >NUL
if not errorlevel 1 (
  ping -n 2 127.0.0.1 >NUL
  goto wait
)
move /Y "{nou}" "{executabil}"
if errorlevel 1 goto gata
if exist "{payload / "uv.lock"}" del /Q "{payload / "uv.lock"}"
del /Q "{payload / "pfasimplu-*.whl"}" 2>NUL
start "" "{executabil}"
:gata
"""


def _script_unix(executabil: Path, nou: Path, payload: Path, pid: int) -> str:
    return f"""#!/bin/sh
# Inlocuirea se face dupa ce procesul Python al aplicatiei s-a oprit.
while kill -0 {pid} 2>/dev/null; do sleep 1; done
sleep 1
mv -f "{nou}" "{executabil}" || exit 1
chmod +x "{executabil}"
rm -f "{payload / "uv.lock"}" 2>/dev/null
rm -f "{payload}"/pfasimplu-*.whl 2>/dev/null
exec "{executabil}"
"""


def pregateste_actualizarea(versiune: str) -> str:
    """Descarca binarul nou si programeaza swap-ul la iesirea aplicatiei."""
    executabil = calea_executabilului()
    if executabil is None:
        raise EroareActualizare(
            "Actualizarea automata este disponibila numai in versiunea standalone."
        )
    payload = executabil.parent / "pycrucible_payload"
    temporar = Path(
        tempfile.mkdtemp(prefix=".pfasimplu-update-", dir=executabil.parent)
    )
    try:
        nou = descarca_executabil(versiune, temporar)
        if os.name == "nt":
            script = temporar / "actualizeaza.bat"
            script.write_text(
                _script_windows(executabil, nou, payload), encoding="utf-8"
            )
            subprocess.Popen(
                ["cmd.exe", "/c", str(script)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            script = temporar / "actualizeaza.sh"
            script.write_text(
                _script_unix(executabil, nou, payload, os.getpid()), encoding="utf-8"
            )
            script.chmod(0o755)
            subprocess.Popen(
                ["/bin/sh", str(script)],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
    except OSError as exc:
        shutil.rmtree(temporar, ignore_errors=True)
        logger.warning("Nu am putut programa actualizarea: %s", exc)
        raise EroareActualizare(
            "Nu am putut programa instalarea actualizarii."
        ) from exc
    except Exception:
        shutil.rmtree(temporar, ignore_errors=True)
        raise
    logger.info("Actualizarea V%s a fost programata pentru %s", versiune, executabil)
    return (
        f"Versiunea V{versiune} a fost descarcata. Se va instala automat cand "
        "inchizi aplicatia, care va reporni cu versiunea noua. Datele tale "
        "nu sunt modificate."
    )
