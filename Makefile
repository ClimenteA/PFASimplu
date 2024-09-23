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

purge-db:
	rm -rf cheltuieli/migrations
	rm -rf documente/migrations
	rm -rf facturi/migrations
	rm -rf incasari/migrations
	rm -rf setari/migrations
	rm stocare.db

package:
	rm -rf public
	mkdir public
	python manage.py collectstatic
	