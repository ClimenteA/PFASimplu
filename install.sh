#!/usr/bin/env bash
# Instalare completa PFASimplu (Linux / macOS):
#   Docker (daca lipseste) -> clone/pull cod -> build -> start pe localhost:8990.
#
# Utilizare:
#   bash <(curl -fsSL https://raw.githubusercontent.com/ClimenteA/PFASimplu/main/install.sh)
#   sau, din repo: ./install.sh
#
# Variabile optionale:
#   PFASIMPLU_DIR      - directorul de instalare (implicit $HOME/PFASimplu)
#   PFASIMPLU_PORT     - port initial (doar daca .env lipseste; altfel editeaza .env)
#   PFASIMPLU_REPO_URL - URL-ul repo-ului (implicit GitHub)

set -euo pipefail

REPO_URL="${PFASIMPLU_REPO_URL:-https://github.com/ClimenteA/PFASimplu.git}"
PORT="${PFASIMPLU_PORT:-8990}"
COMPOSE_FILE="docker-compose-local.yaml"

log()  { printf '\n==> %s\n' "$*"; }
warn() { printf 'ATENTIE: %s\n' "$*" >&2; }
die()  { printf 'EROARE: %s\n' "$*" >&2; exit 1; }

OS="$(uname -s)"
case "$OS" in
    Linux*)  PLATFORM=linux ;;
    Darwin*) PLATFORM=mac ;;
    *)       die "Sistem de operare nesuportat: $OS. Foloseste install.bat pe Windows." ;;
esac

# Daca scriptul e deja intr-un checkout, folosim acel director. Altfel clonam.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
    INSTALL_DIR="$SCRIPT_DIR"
else
    INSTALL_DIR="${PFASIMPLU_DIR:-$HOME/PFASimplu}"
fi

# ---------------------------------------------------------------------------
# 1. Docker
# ---------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    log "Docker nu este instalat. Il instalez..."
    if [ "$PLATFORM" = "mac" ]; then
        if command -v brew >/dev/null 2>&1; then
            brew install --cask docker
        else
            die "Instaleaza Docker Desktop de la https://www.docker.com/products/docker-desktop/ si re-ruleaza scriptul."
        fi
        open -a Docker 2>/dev/null || true
    else
        if ! command -v curl >/dev/null 2>&1; then
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y curl
            else
                die "Instaleaza curl si re-ruleaza scriptul."
            fi
        fi
        curl -fsSL https://get.docker.com | sh
        if [ -n "${USER:-}" ] && [ "$USER" != "root" ]; then
            sudo usermod -aG docker "$USER" 2>/dev/null || true
            warn "Utilizatorul $USER a fost adaugat in grupul 'docker'. Deschide un terminal nou daca docker cere sudo."
        fi
    fi
else
    log "Docker este deja instalat."
fi

# asteapta daemonul (pe Mac Docker Desktop porneste la cateva secunde dupa install)
log "Verific Docker..."
DOCKER_READY=0
for _ in $(seq 1 60); do
    if docker info >/dev/null 2>&1; then
        DOCKER_READY=1
        break
    fi
    sleep 2
done
[ "$DOCKER_READY" -eq 1 ] || die "Docker nu raspunde. Porneste Docker (Desktop/daemon) si re-ruleaza scriptul."
docker compose version >/dev/null 2>&1 || die "Instaleaza Docker Compose v2 (pluginul 'docker compose') si re-ruleaza."

# ---------------------------------------------------------------------------
# 2. Codul
# ---------------------------------------------------------------------------
if ! command -v git >/dev/null 2>&1; then
    log "git nu este instalat. Il instalez..."
    if [ "$PLATFORM" = "mac" ]; then
        xcode-select --install 2>/dev/null || true
        die "Instaleaza git (xcode-select --install / brew install git) si re-ruleaza scriptul."
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y git
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm git
    else
        die "Instaleaza git si re-ruleaza scriptul."
    fi
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    log "Actualizez codul in $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only
elif [ -e "$INSTALL_DIR" ]; then
    die "Directorul $INSTALL_DIR exista dar nu e un repo git. Alege alt director cu PFASIMPLU_DIR."
else
    log "Clonez codul in $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# Directoarele de date montate in containere (le creem ca utilizator, nu ca root).
mkdir -p src/dbsqlite src/media staticfiles

# Porturile se citesc din .env (fisierul e versionat cu valori mock), ca sa
# nu existe diferenta intre ce afiseaza scriptul si ce foloseste Compose.
if [ -f .env ]; then
    ENV_PORT="$(sed -n 's/^PFASIMPLU_PORT=\([0-9][0-9]*\).*/\1/p' .env | head -n1)"
    [ -n "$ENV_PORT" ] && PORT="$ENV_PORT"
    ENV_MCP_PORT="$(sed -n 's/^PFASIMPLU_MCP_PORT=\([0-9][0-9]*\).*/\1/p' .env | head -n1)"
    [ -n "$ENV_MCP_PORT" ] && PFASIMPLU_MCP_PORT="$ENV_MCP_PORT"
fi
export PFASIMPLU_PORT="$PORT"

# ---------------------------------------------------------------------------
# 3. Configurare + build + pornire
# ---------------------------------------------------------------------------
# .env e versionat cu valori mock (nimic secret); il cream doar daca lipseste.
if [ ! -f .env ]; then
    log "Creez .env cu valorile implicite (port ${PORT})"
    cat > .env <<EOF_ENV
PFASIMPLU_PORT=${PORT}
PFASIMPLU_MCP_PORT=${PFASIMPLU_MCP_PORT:-8997}
PFASIMPLU_SECRET_KEY=local-mock-secret-key-schimba-ma-daca-vrei-esti-in-regula
PFASIMPLU_DEBUG=0
PFASIMPLU_SECURE_COOKIES=0
PFASIMPLU_ALLOWED_HOSTS=localhost,127.0.0.1
PFASIMPLU_CSRF_TRUSTED_ORIGINS=http://localhost:${PORT},http://127.0.0.1:${PORT}
EOF_ENV
fi

log "Build si pornire (docker compose)..."
docker compose -f "$COMPOSE_FILE" up -d --build

log "Verific aplicatia..."
if command -v curl >/dev/null 2>&1; then
    for _ in $(seq 1 60); do
        if curl -fsS "http://localhost:${PORT}/conturi/login/" >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
fi

cat <<EOF

Gata! PFASimplu ruleaza la http://localhost:${PORT}

  * Logarea este obligatorie: creeaza cont la
    http://localhost:${PORT}/conturi/inregistrare/
  * Datele sunt pe gazda, in $(pwd)/src/dbsqlite/ (baza de date) si
    $(pwd)/src/media/ (fisierele urcate/generate) -> fa backup la aceste foldere.
  * Oprire:   docker compose -f ${COMPOSE_FILE} down
  * Loguri:   docker compose -f ${COMPOSE_FILE} logs -f
  * Actualizare: ruleaza din nou acest script (face git pull + rebuild).
EOF
