.PHONY: dev devdb test-e2e migrate-all purge-migration-dirs purge-db package build-local start-local stop-local logs-local build start stop logs mcp-local mcp-http package-mcp lint format ruff check

# Sursele aplicatiei sunt in src/ (app-uri Django, core, mcp_server, etc.).
# Comenzile de mai jos ruleaza din radacina repo-ului, deci folosim calea
# explicita catre src/manage.py si PYTHONPATH=src pentru modulele python -m.


dev:
	uv run src/manage.py runserver 8990

devdb:
	PFASIMPLU_DB_PATH=src/tests/.runtime/test.db PFASIMPLU_MEDIA_ROOT=src/tests/.runtime/files uv run src/manage.py runserver 8990

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

package:
	rm -rf build
	rm -rf dist
	rm -f pfasimplu.spec
	make purge-db
	make migrate-all
	make purge-migration-dirs
	uv run pyinstaller --noconfirm --name pfasimplu --icon src/icon.png --paths src --add-data "src/dbsqlite:dbsqlite" --add-data "src/templates:templates" --add-data "src/static:static" --add-data "pyproject.toml:." --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr src/gui.py
	mkdir ./dist/pfasimplu/_internal/media


# Docker local (mereu pornit, http://localhost:8996; port prin PFASIMPLU_PORT).
build-local:
	docker compose -f server/docker-compose-local.yml build

start-local:
	docker compose -f server/docker-compose-local.yml up -d --build

stop-local:
	docker compose -f server/docker-compose-local.yml down

logs-local:
	docker compose -f server/docker-compose-local.yml logs -f --tail=100

# Docker prod (aplicatie + Caddy, pe VPS; necesita server/.env.prod).
build:
	docker compose -f server/docker-compose.yml build

start:
	docker compose -f server/docker-compose.yml up -d --build

stop:
	docker compose -f server/docker-compose.yml down

logs:
	docker compose -f server/docker-compose.yml logs -f --tail=100

# Server MCP stdio pentru aplicatia locala (cheia se pune in mediu):
#   PFASIMPLU_MCP_TOKEN=<cheia din /setari> make mcp-local
mcp-local:
	PYTHONPATH=src uv run python -m mcp_server.local

# Server MCP HTTP local, fara Docker (http://localhost:8001/mcp).
mcp-http:
	PYTHONPATH=src uv run python -m uvicorn mcp_server.http_app:app --host 127.0.0.1 --port 8001

# Executabil separat pentru serverul MCP stdio (alternativa la sursa).
package-mcp:
	rm -rf build dist
	uv run pyinstaller --noconfirm --name pfasimplu-mcp --icon src/icon.png --console --paths src \
		--add-data "src/dbsqlite:dbsqlite" --add-data "src/templates:templates" --add-data "src/static:static" --add-data "pyproject.toml:." \
		--collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib \
		--collect-all django_browser_reload --collect-all cattr --collect-all fastmcp \
		src/mcp_stdio_main.py
	mkdir -p ./dist/pfasimplu-mcp/_internal/media
