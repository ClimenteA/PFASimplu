dev:
	uv run manage.py runserver

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
