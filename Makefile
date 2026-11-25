.PHONY: install dev dev-e2e dev-superuser test-e2e migrate-all purge-migration-dirs purge-db build-local start-local stop-local logs-local build start stop logs format lint ruff check

# Sursele aplicatiei sunt in src/. Comenzile de mai jos ruleaza din radacina
# repo-ului, deci folosim calea explicita catre src/manage.py si PYTHONPATH=src
# pentru modulele python -m.
# Pentru utilizatori aplicatia ruleaza in Docker (docker-compose*.yaml).
# `make dev` e doar pentru dezvoltare, cu date separate de cele din Docker.

# Instalare completa (Docker + clone + build + start) pentru uz local.
install:
	./install.sh

# Dezvoltare cu uv run: server cu auto-reload pe http://127.0.0.1:8990.
# Foloseste aceeasi baza de date si acelasi folder media ca Docker-ul local
# (src/dbsqlite/stocare.db si src/media/) - datele nu se pierd la trecerea
# de la `make dev` la `make start-local`. Opreste intai containerul local
# daca vrei sa rulezi pe acelasi port.
DEV_PORT ?= 8990

dev:
	uv run src/manage.py migrate --noinput
	uv run src/manage.py runserver $(DEV_PORT)

# Ruleaza aplicatia pe baza de date lasata de `make test-e2e`, pe acelasi port
# ca `make dev`. Datele reale (src/dbsqlite/stocare.db) nu sunt atinse.
# Login: test@pfasimplu.ro / parola-test-e2e-123 (contul creat de teste).
dev-e2e:
	test -f src/tests/.runtime/test.db || (echo "Ruleaza intai make test-e2e"; exit 1)
	PFASIMPLU_DB_PATH=src/tests/.runtime/test.db uv run src/manage.py runserver $(DEV_PORT)

# Cont de admin pentru /admin/ (in aceeasi baza de date).
dev-superuser:
	uv run src/manage.py createsuperuser

# Docker local, fara Caddy, mereu pornit (http://localhost:8990;
# port prin PFASIMPLU_PORT).
build-local:
	docker compose -f docker-compose-local.yaml build

start-local:
	docker compose -f docker-compose-local.yaml up -d --build

stop-local:
	docker compose -f docker-compose-local.yaml down

logs-local:
	docker compose -f docker-compose-local.yaml logs -f --tail=100

# Docker prod (aplicatie + Caddy, pe VPS; necesita server/.env.prod).
build:
	docker compose -f docker-compose.yaml build

start:
	docker compose -f docker-compose.yaml up -d --build

stop:
	docker compose -f docker-compose.yaml down

logs:
	docker compose -f docker-compose.yaml logs -f --tail=100

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
	rm src/dbsqlite/stocare.db

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
