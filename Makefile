.PHONY: dev dev-e2e dev-superuser test-e2e migrate-all purge-migration-dirs purge-db build-local start-local restart-local stop-local logs-local build start restart stop logs format lint ruff check dist

# Sursele aplicatiei sunt in src/. Comenzile de mai jos ruleaza din radacina
# repo-ului, deci folosim calea explicita catre src/manage.py si PYTHONPATH=src
# pentru modulele python -m.
# Pentru utilizare zilnica, aplicatia desktop se descarca din GitHub Releases.
# Docker (docker-compose*.yaml) si `make dev` sunt pentru dezvoltare / self-hosting.

# Dezvoltare cu uv run: server cu auto-reload pe http://127.0.0.1:8990.
# Foloseste aceeasi baza de date si acelasi folder media ca Docker-ul local
# (appdata/db/stocare.db si appdata/files/) - datele nu se pierd la trecerea
# de la `make dev` la `make start-local`. Opreste intai containerul local
# daca vrei sa rulezi pe acelasi port.
DEV_PORT ?= 8990

dev:
	uv run src/manage.py migrate --noinput
	uv run src/manage.py runserver $(DEV_PORT)

# Ruleaza aplicatia pe baza de date lasata de `make test-e2e`, pe acelasi port
# ca `make dev`. Datele reale (appdata/db/stocare.db) nu sunt atinse.
# Login: test@pfasimplu.ro / parola-test-e2e-123 (contul creat de teste).
dev-e2e:
	test -f src/tests/.runtime/test.db || (echo "Ruleaza intai make test-e2e"; exit 1)
	PFASIMPLU_DB_PATH=src/tests/.runtime/test.db uv run src/manage.py runserver $(DEV_PORT)

# Cont de admin pentru /admin/ (in aceeasi baza de date).
dev-superuser:
	uv run src/manage.py createsuperuser

# Docker local, fara Caddy, mereu pornit (http://localhost:8990;
# port prin PFASIMPLU_PORT).
# Codul sursa e montat live din ./src in container, deci editarile de cod nu
# necesita rebuild. `start-local` construieste imaginea doar daca nu exista;
# pentru schimbari de dependinte (pyproject.toml/uv.lock) sau Dockerfile foloseste
# `build-local`. Dupa editari de cod, `restart-local` recreeaza containerul ca
# waitress sa incarce codul nou (nu are auto-reload).
build-local:
	docker compose -f docker-compose-local.yaml build

start-local:
	docker compose -f docker-compose-local.yaml up -d

restart-local:
	docker compose -f docker-compose-local.yaml up -d --force-recreate

stop-local:
	docker compose -f docker-compose-local.yaml down

logs-local:
	docker compose -f docker-compose-local.yaml logs -f --tail=100

# Docker prod (aplicatie + Caddy, pe VPS; necesita .env.prod).
# Aceeasi logica: codul e montat live, asa ca dupa un `git pull` e suficient
# `restart`; `build` ramane pentru schimbari de dependinte/Dockerfile.
build:
	docker compose -f docker-compose.yaml build

start:
	docker compose -f docker-compose.yaml up -d

restart:
	docker compose -f docker-compose.yaml up -d --force-recreate

stop:
	docker compose -f docker-compose.yaml down

logs:
	docker compose -f docker-compose.yaml logs -f --tail=100

# Executabil standalone pentru OS-ul curent: wheel + PyCrucible (build-time
# only, prin uvx). Rezultatul apare in dist/; vezi si scripts/smoke_dist.py.
dist:
	uv run --no-project python scripts/build_dist.py

# Migrari (versionate in git; utile cand modifice modelele in dezvoltare).
migrate-all:
	uv run src/manage.py makemigrations utils
	uv run src/manage.py makemigrations
	uv run src/manage.py migrate
	uv run src/manage.py makemigrations cheltuieli
	uv run src/manage.py makemigrations documente
	uv run src/manage.py makemigrations facturi
	uv run src/manage.py makemigrations incasari
	uv run src/manage.py makemigrations setari
	uv run src/manage.py migrate cheltuieli
	uv run src/manage.py migrate documente
	uv run src/manage.py migrate facturi
	uv run src/manage.py migrate incasari
	uv run src/manage.py migrate setari

purge-migration-dirs:
	rm -rf src/utils/migrations
	rm -rf src/cheltuieli/migrations
	rm -rf src/documente/migrations
	rm -rf src/facturi/migrations
	rm -rf src/incasari/migrations
	rm -rf src/setari/migrations

purge-db:
	make purge-migration-dirs
	rm appdata/db/stocare.db

test-e2e:
	uv run playwright install chromium
	uv run pytest src/tests -v

# Ruff: formatare si lint (reguli implicite Ruff).
format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

# Ruleaza formatarea si corectarile lint intr-o singura comanda.
ruff: format lint

# Verificare fara modificari (utila in CI).
check:
	uv run ruff format --check .
	uv run ruff check .
