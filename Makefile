migrate-all:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py migrate cheltuieli 
	python manage.py migrate documente 
	python manage.py migrate facturi
	python manage.py migrate incasari
	python manage.py migrate setari

run:
	python manage.py runserver