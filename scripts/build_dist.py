"""Construieste executabilul standalone pentru OS-ul curent.

Pipeline: `uv build --wheel` -> copiaza wheel-ul in dist-build/ -> PyCrucible
embeds proiectul mic (launcher.py + pyproject.toml + wheel) -> binar in dist/.
PyCrucible este doar tool de build, instalat prin uvx, nu dependenta aplicatiei.
"""

import hashlib
import logging
import platform
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
LAUNCHER_DIR = ROOT / "dist-build"
PYCRUCIBLE_VERSION = "0.4.8"
UV_VERSION = "0.9.21"

# dist-build/ e gitignorat (contine wheel-ul copiat si .venv-ul generat), deci
# proiectul mic embed-uit de PyCrucible trebuie creat la fiecare build, altfel
# pe un checkout curat (CI) nu exista nici macar directorul.
LAUNCHER_PY = '''"""Entrypoint pentru proiectul mic embed-uit de PyCrucible.

Wheel-ul pfasimplu este instalat de uv in venv-ul proiectului, deci modulul
core.launcher vine din pachet, nu din acest director.
"""

from core.launcher import main

if __name__ == "__main__":
    main()
'''

LAUNCHER_PYPROJECT = """[project]
name = "pfasimplu-launcher"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = ["pfasimplu"]

# Proiectul nu se instaleaza ca pachet; doar rezolva wheel-ul pfasimplu din
# directorul curent (copiat aici de scripts/build_dist.py) si dependentele lui.
[tool.uv]
package = false
find-links = ["."]

[tool.pycrucible]
entrypoint = "launcher.py"

[tool.pycrucible.options]
extract_to_temp = false
delete_after_run = false
uv_version = "{UV_VERSION}"

[tool.pycrucible.patterns]
include = ["*.py", "**/*.py", "*.whl"]
exclude = [".venv/**/*", "**/__pycache__/**", "**/*.pyc"]
"""

log = logging.getLogger("build_dist")


def target_name(version: str) -> str:
    system = platform.system().lower()
    os_name = {"darwin": "macos", "windows": "windows", "linux": "linux"}.get(
        system, system
    )
    machine = platform.machine().lower()
    arch = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)
    suffix = ".exe" if os_name == "windows" else ""
    return f"pfasimplu-{version}-{os_name}-{arch}{suffix}"


def run(command: list[str]) -> None:
    log.info("$ %s", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def prepare_launcher(version: str) -> None:
    """Creeaza proiectul PyCrucible, fara sa depinda de fisiere gitignorate."""
    LAUNCHER_DIR.mkdir(parents=True, exist_ok=True)

    # Curatam reziduurile unei rulari anterioare: un uv.lock sau .venv vechi
    # ar trimite la alt wheel decat cel proaspat construit.
    for stale in (LAUNCHER_DIR / ".venv", LAUNCHER_DIR / "uv.lock"):
        if stale.is_dir():
            shutil.rmtree(stale)
        elif stale.exists():
            stale.unlink()
    for old in LAUNCHER_DIR.glob("*.whl"):
        old.unlink()
    shutil.rmtree(LAUNCHER_DIR / "__pycache__", ignore_errors=True)

    (LAUNCHER_DIR / "launcher.py").write_text(LAUNCHER_PY, encoding="utf-8")
    (LAUNCHER_DIR / "pyproject.toml").write_text(
        LAUNCHER_PYPROJECT.format(UV_VERSION=UV_VERSION),
        encoding="utf-8",
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]

    uv = shutil.which("uv") or "uv"
    uvx = shutil.which("uvx") or "uvx"

    DIST.mkdir(exist_ok=True)
    run([uv, "build", "--wheel", "--out-dir", str(DIST)])

    wheels = sorted(DIST.glob(f"pfasimplu-{version}-*.whl"))
    if not wheels:
        raise SystemExit(f"Nu am gasit wheel-ul pfasimplu-{version} in {DIST}")
    wheel = wheels[-1]

    prepare_launcher(version)

    # uv tine in cache wheel-urile locale dupa nume. Un build tag derivat din
    # continut schimba numele cand se modifica codul, deci o reconstruire cu
    # aceeasi versiune nu ajunge la un wheel vechi (si nu e nevoie de
    # `uv cache clean`, care ar blocase lock-ul lui `uv run` parinte).
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()[:8]
    build_tag = f"1{int(digest, 16) % 10**8:07d}"
    name, version_part, *tags = wheel.stem.split("-")
    embedded_name = f"{name}-{version_part}-{build_tag}-{'-'.join(tags)}.whl"
    shutil.copy2(wheel, LAUNCHER_DIR / embedded_name)
    log.info("Wheel copiat in %s", LAUNCHER_DIR / embedded_name)

    output = DIST / target_name(version)
    if output.exists():
        output.unlink()

    run(
        [
            uvx,
            "--from",
            f"pycrucible=={PYCRUCIBLE_VERSION}",
            "pycrucible",
            "--embed",
            str(LAUNCHER_DIR),
            "--output",
            str(output),
            "--uv-version",
            UV_VERSION,
        ]
    )

    if not output.exists():
        raise SystemExit(f"PyCrucible nu a produs {output}")
    log.info("Executabil: %s", output)

    # Release-urile contin arhiva; executabilul raman e in dist/ pentru smoke
    # test si pentru rularea locala.
    # with_suffix() ar taia ".0" din versiune, deci construim numele explicit.
    base_name = output.name[:-4] if output.name.endswith(".exe") else output.name
    archive_path = DIST / f"{base_name}.zip"
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(output, arcname=output.name)
    log.info("Arhiva: %s", archive_path)


if __name__ == "__main__":
    sys.exit(main())
