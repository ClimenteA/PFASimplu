@echo off
REM This batch file executes the commands from the Makefile

REM Check if an argument is provided
IF "%1"=="" (
    echo Usage: %0 [command]
    exit /b
)

REM Execute the specified command
IF "%1"=="run" (
    python manage.py runserver
) ELSE IF "%1"=="migrate-all" (

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

) ELSE IF "%1"=="purge-migration-dirs" (

    rmdir /s /q cheltuieli\migrations
	rmdir /s /q documente\migrations
	rmdir /s /q facturi\migrations
	rmdir /s /q incasari\migrations
	rmdir /s /q setari\migrations

) ELSE IF "%1"=="purge-db" (

    call %0 purge-migration-dirs
    del dbsqlite\stocare.db

) ELSE IF "%1"=="package" (

    call %0 purge-db
    call %0 migrate-all
    call %0 purge-migration-dirs
    pyinstaller --name pfasimplu --icon icon.png --add-data "dbsqlite;dbsqlite" --add-data "templates;templates" --add-data "static;static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload gui.py
    mkdir dist\pfasimplu\_internal\media

) ELSE (
    echo Invalid command. Available commands: run, migrate-all, purge-migration-dirs, purge-db, package
)
