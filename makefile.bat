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
    pyinstaller --noconfirm --name pfasimplu --icon icon.png --add-data "dbsqlite;dbsqlite" --add-data "templates;templates" --add-data "static;static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr gui.py
    mkdir .\dist\pfasimplu\_internal\media

) ELSE IF "%1"=="mcp-local" (
    python -m mcp_server.local
) ELSE IF "%1"=="mcp-http" (
    python -m uvicorn mcp_server.http_app:app --host 127.0.0.1 --port 8001
) ELSE IF "%1"=="package-mcp" (
    pyinstaller --noconfirm --name pfasimplu-mcp --icon icon.png --console --add-data "dbsqlite;dbsqlite" --add-data "templates;templates" --add-data "static;static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr --collect-all fastmcp mcp_stdio_main.py
    mkdir .\dist\pfasimplu-mcp\_internal\media
) ELSE (
    echo Invalid command. Available commands: run, migrate-all, purge-migration-dirs, purge-db, package, mcp-local, mcp-http
)
