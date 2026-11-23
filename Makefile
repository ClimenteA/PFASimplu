.PHONY: dev build-local start-local stop-local logs-local build start stop logs


dev:
	uv run manage.py runserver 8990

devdb:
	PFASIMPLU_DB_PATH=tests/.runtime/test.db PFASIMPLU_MEDIA_ROOT=tests/.runtime/files uv run manage.py runserver 8990

test-e2e:
	uv run playwright install chromium
	uv run pytest tests/ -v

migrate-all:
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
