run:
	python manage.py runserver

migrate-all:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py makemigrations cheltuieli 
	python manage.py makemigrations documente 
	python manage.py makemigrations facturi
	python manage.py makemigrations incasari
	python manage.py makemigrations setari
	python manage.py migrate cheltuieli 
	python manage.py migrate documente 
	python manage.py migrate facturi
	python manage.py migrate incasari
	python manage.py migrate setari

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
	pyinstaller --name pfasimplu --icon icon.png --add-data "dbsqlite:dbsqlite" --add-data "templates:templates" --add-data "static:static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload gui.py
	mkdir /dist/pfasimplu/_internal/media
	