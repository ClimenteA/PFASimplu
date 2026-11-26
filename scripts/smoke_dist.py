"""Smoke test pentru binarul produs de `make dist`.

Copiaza executabilul intr-un director temporar, il porneste fara fereastra de
browser, asteapta pagina de login si verifica faptul ca baza SQLite a fost
creata in directorul de date, nu in repo. Primul start poate descarca Python
si dependentele prin uv, deci timeout-ul este generos.
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TIMEOUT_SECONDS = 900


def find_binary(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = [
        item
        for item in path.iterdir()
        if item.is_file()
        and item.name.startswith("pfasimplu-")
        and item.suffix not in (".whl", ".zip", ".txt", ".json", ".md")
    ]
    if not candidates:
        raise SystemExit(f"Nu am gasit niciun executabil in {path}")
    return max(candidates, key=lambda item: item.stat().st_mtime)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop(process: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            check=False,
        )
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "binary",
        nargs="?",
        default=str(DIST),
        help="executabilul sau directorul dist/ (implicit)",
    )
    args = parser.parse_args()

    binary = find_binary(Path(args.binary))
    port = free_port()

    with tempfile.TemporaryDirectory(prefix="pfasimplu-smoke-") as tmp:
        tmp_path = Path(tmp)
        local_binary = tmp_path / binary.name
        local_binary.write_bytes(binary.read_bytes())
        local_binary.chmod(0o755)

        data_dir = tmp_path / "data"
        env = os.environ.copy()
        env.update(
            {
                "PFASIMPLU_DATA_DIR": str(data_dir),
                "PFASIMPLU_NO_BROWSER": "1",
                "PFASIMPLU_PORT": str(port),
            }
        )

        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        process = subprocess.Popen(
            [str(local_binary)],
            cwd=tmp_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            **kwargs,
        )

        url = f"http://127.0.0.1:{port}/conturi/login/"
        deadline = time.monotonic() + TIMEOUT_SECONDS
        ready = False
        try:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen(url, timeout=3) as response:
                        ready = response.status < 500
                        if ready:
                            break
                except (urllib.error.URLError, ConnectionError, OSError):
                    time.sleep(1)

            if not ready:
                print("Serverul nu a raspuns la", url)
                return 1

            db_path = data_dir / "db" / "stocare.db"
            checks = {
                "baza SQLite in directorul de date": db_path.is_file(),
                "cheia secreta persistata": (data_dir / "secret_key").is_file(),
                "fisiere statice colectate": (data_dir / "staticfiles").is_dir(),
            }
            for label, ok in checks.items():
                print(("OK  " if ok else "FAIL"), label)
            if not all(checks.values()):
                return 1
            print("OK  pagina de login:", url)
            return 0
        finally:
            stop(process)
            output = process.stdout.read() if process.stdout else ""
            if output:
                print("--- ultimele linii din executabil ---")
                print("\n".join(output.splitlines()[-20:]))


if __name__ == "__main__":
    sys.exit(main())
