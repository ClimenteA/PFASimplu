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

run:
	python manage.py runserver