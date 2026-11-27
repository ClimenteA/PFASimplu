@echo off
REM Echivalentul pe Windows pentru comenzile din Makefile.
REM Pentru utilizatori aplicatia ruleaza in Docker; install.bat face instalarea.
REM `dev` ruleaza serverul cu uv/python, pe datele din src\ (ca Docker-ul).

IF "%1"=="" (
    echo Usage: %0 [command]
    exit /b
)

IF "%1"=="dev" (
    python src\manage.py migrate --noinput
    python src\manage.py runserver 8990
) ELSE IF "%1"=="dev-superuser" (
    python src\manage.py createsuperuser
) ELSE IF "%1"=="start-local" (
    docker compose -f docker-compose-local.yaml up -d
) ELSE IF "%1"=="restart-local" (
    REM Codul e montat live: repornim fara rebuild dupa editari.
    docker compose -f docker-compose-local.yaml up -d --force-recreate
) ELSE IF "%1"=="stop-local" (
    docker compose -f docker-compose-local.yaml down
) ELSE IF "%1"=="logs-local" (
    docker compose -f docker-compose-local.yaml logs -f --tail=100
) ELSE IF "%1"=="migrate-all" (
    python src\manage.py makemigrations utils
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
    del appdata\db\stocare.db
) ELSE (
    echo Invalid command. Available commands: dev, dev-superuser, start-local, restart-local, stop-local, logs-local, migrate-all, purge-migration-dirs, purge-db
)
