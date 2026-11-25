.PHONY: dev devdb test-e2e migrate-all purge-migration-dirs purge-db package build-local start-local stop-local logs-local build start stop logs mcp-local mcp-http package-mcp lint format ruff check


dev:
	uv run manage.py runserver 8990

devdb:
	PFASIMPLU_DB_PATH=tests/.runtime/test.db PFASIMPLU_MEDIA_ROOT=tests/.runtime/files uv run manage.py runserver 8990

test-e2e:
	uv run playwright install chromium
	uv run pytest tests/ -v

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
	uv run manage.py makemigrations utils
	uv run manage.py makemigrations
	uv run manage.py migrate
	uv run manage.py makemigrations cheltuieli 
	uv run manage.py makemigrations documente 
	uv run manage.py makemigrations facturi
	uv run manage.py makemigrations incasari
	uv run manage.py makemigrations setari
	uv run manage.py migrate cheltuieli 
	uv run manage.py migrate documente 
	uv run manage.py migrate facturi
	uv run manage.py migrate incasari
	uv run manage.py migrate setari

purge-migration-dirs:
	rm -rf utils/migrations
	rm -rf cheltuieli/migrations
	rm -rf documente/migrations
	rm -rf facturi/migrations
	rm -rf incasari/migrations
	rm -rf setari/migrations

purge-db:
	make purge-migration-dirs
	rm dbsqlite/stocare.db

package:
	rm -rf build
	rm -rf dist
	rm -f pfasimplu.spec
	make purge-db
	make migrate-all
	make purge-migration-dirs
	uv run pyinstaller --noconfirm --name pfasimplu --icon icon.png --add-data "dbsqlite:dbsqlite" --add-data "templates:templates" --add-data "static:static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr gui.py
	mkdir ./dist/pfasimplu/_internal/media


# Docker local (mereu pornit, http://localhost:8996; port prin PFASIMPLU_PORT).
build-local:
	docker compose -f docker-compose-local.yml build

start-local:
	docker compose -f docker-compose-local.yml up -d --build

stop-local:
	docker compose -f docker-compose-local.yml down

logs-local:
	docker compose -f docker-compose-local.yml logs -f --tail=100

# Docker prod (aplicatie + Caddy, pe VPS; necesita .env.prod).
build:
	docker compose build

start:
	docker compose up -d --build

stop:
	docker compose down

logs:
	docker compose logs -f --tail=100

# Server MCP stdio pentru aplicatia locala (cheia se pune in mediu):
#   PFASIMPLU_MCP_TOKEN=<cheia din /setari> make mcp-local
mcp-local:
	uv run python -m mcp_server.local

# Server MCP HTTP local, fara Docker (http://localhost:8001/mcp).
mcp-http:
	uv run python -m uvicorn mcp_server.http_app:app --host 127.0.0.1 --port 8001

# Executabil separat pentru serverul MCP stdio (alternativa la sursa).
package-mcp:
	rm -rf build dist
	uv run pyinstaller --noconfirm --name pfasimplu-mcp --icon icon.png --console \
		--add-data "dbsqlite:dbsqlite" --add-data "templates:templates" --add-data "static:static" \
		--collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib \
		--collect-all django_browser_reload --collect-all cattr --collect-all fastmcp \
		mcp_stdio_main.py
	mkdir -p ./dist/pfasimplu-mcp/_internal/media
