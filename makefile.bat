@echo off
REM This batch file executes the commands from the Makefile
REM Sursele aplicatiei sunt in src\.

REM Check if an argument is provided
IF "%1"=="" (
    echo Usage: %0 [command]
    exit /b
)

REM Execute the specified command
IF "%1"=="run" (
    python src\manage.py runserver
) ELSE IF "%1"=="migrate-all" (

    python src\manage.py makemigrations
    python src\manage.py migrate
    python src\manage.py makemigrations cheltuieli
    python src\manage.py makemigrations documente
    python src\manage.py makemigrations facturi
    python src\manage.py makemigrations incasari
    python src\manage.py makemigrations setari
    python src\manage.py migrate cheltuieli
    python src\manage.py migrate documente
    python src\manage.py migrate facturi
    python src\manage.py migrate incasari
    python src\manage.py migrate setari

) ELSE IF "%1"=="purge-migration-dirs" (

    rmdir /s /q src\utils\migrations
    rmdir /s /q src\cheltuieli\migrations
    rmdir /s /q src\documente\migrations
    rmdir /s /q src\facturi\migrations
    rmdir /s /q src\incasari\migrations
    rmdir /s /q src\setari\migrations

) ELSE IF "%1"=="purge-db" (

    call %0 purge-migration-dirs
    del src\dbsqlite\stocare.db

) ELSE IF "%1"=="package" (

    call %0 purge-db
    call %0 migrate-all
    call %0 purge-migration-dirs
    pyinstaller --noconfirm --name pfasimplu --icon src\icon.png --paths src --add-data "src\dbsqlite;dbsqlite" --add-data "src\templates;templates" --add-data "src\static;static" --add-data "pyproject.toml;." --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr src\gui.py
    mkdir .\dist\pfasimplu\_internal\media

) ELSE IF "%1"=="mcp-local" (
    set PYTHONPATH=src&& python -m mcp_server.local
) ELSE IF "%1"=="mcp-http" (
    set PYTHONPATH=src&& python -m uvicorn mcp_server.http_app:app --host 127.0.0.1 --port 8001
) ELSE IF "%1"=="package-mcp" (
    pyinstaller --noconfirm --name pfasimplu-mcp --icon src\icon.png --console --paths src --add-data "src\dbsqlite;dbsqlite" --add-data "src\templates;templates" --add-data "src\static;static" --add-data "pyproject.toml;." --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload --collect-all cattr --collect-all fastmcp src\mcp_stdio_main.py
    mkdir .\dist\pfasimplu-mcp\_internal\media
) ELSE (
    echo Invalid command. Available commands: run, migrate-all, purge-migration-dirs, purge-db, package, mcp-local, mcp-http, package-mcp
)
