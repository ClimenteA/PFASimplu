@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Instalare completa PFASimplu (Windows): Docker Desktop + git + build + start.
REM Ruleaza din PowerShell sau cmd: install.bat
REM Optionale: PFASIMPLU_DIR (director), PFASIMPLU_PORT (port, implicit 8990).

set "REPO_URL=https://github.com/ClimenteA/PFASimplu.git"
set "INSTALL_DIR=%USERPROFILE%\PFASimplu"
if defined PFASIMPLU_DIR set "INSTALL_DIR=%PFASIMPLU_DIR%"
set "PORT=8990"
if defined PFASIMPLU_PORT set "PORT=%PFASIMPLU_PORT%"

echo.
echo == Verific Docker ==
where docker >nul 2>nul
if errorlevel 1 (
    echo Docker nu este instalat. Instalez Docker Desktop prin winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo Instaleaza manual Docker Desktop de la https://www.docker.com/products/docker-desktop/ si re-ruleaza acest script.
        exit /b 1
    )
    winget install --id Docker.DockerDesktop -e --accept-package-agreements --accept-source-agreements
    echo Porneste Docker Desktop, asteapta sa fie ready, apoi RE-RULEAZA acest script.
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    exit /b 0
)

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker exista dar nu raspunde. Porneste Docker Desktop si re-ruleaza scriptul.
    exit /b 0
)
docker compose version >nul 2>nul
if errorlevel 1 (
    echo Docker Compose v2 lipseste. Actualizeaza Docker Desktop si re-ruleaza.
    exit /b 1
)
echo Docker OK.

echo.
echo == Verific git ==
where git >nul 2>nul
if errorlevel 1 (
    echo git nu este instalat. Il instalez prin winget...
    winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
    echo RE-RULEAZA acest script dupa instalare.
    exit /b 0
)

echo.
echo == Codul ==
if exist "%INSTALL_DIR%\.git" (
    echo Actualizez codul in %INSTALL_DIR%
    git -C "%INSTALL_DIR%" pull --ff-only
) else (
    if exist "%INSTALL_DIR%" (
        echo EROARE: directorul %INSTALL_DIR% exista dar nu e un repo git.
        echo Alege alt director cu PFASIMPLU_DIR.
        exit /b 1
    )
    echo Clonez codul in %INSTALL_DIR%
    git clone "%REPO_URL%" "%INSTALL_DIR%"
)
cd /d "%INSTALL_DIR%"

REM Directoarele montate in containere (create de utilizator, nu de root).
if not exist "src\dbsqlite" mkdir "src\dbsqlite"
if not exist "src\media" mkdir "src\media"
if not exist "staticfiles" mkdir "staticfiles"

REM Portul aplicatiei se citeste din .env (daca exista).
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if "%%A"=="PFASIMPLU_PORT" set "PORT=%%B"
    )
)

echo.
echo == Configurare ==
REM .env e versionat cu valori mock (nimic secret); il cream doar daca lipseste.
if not exist ".env" (
    > ".env" echo PFASIMPLU_PORT=%PORT%
    >> ".env" echo PFASIMPLU_MCP_PORT=8997
    >> ".env" echo PFASIMPLU_SECRET_KEY=local-mock-secret-key-schimba-ma-daca-vrei-esti-in-regula
    >> ".env" echo PFASIMPLU_DEBUG=0
    >> ".env" echo PFASIMPLU_SECURE_COOKIES=0
    >> ".env" echo PFASIMPLU_ALLOWED_HOSTS=localhost,127.0.0.1
    >> ".env" echo PFASIMPLU_CSRF_TRUSTED_ORIGINS=http://localhost:%PORT%,http://127.0.0.1:%PORT%
)

echo.
echo == Build si pornire ==
docker compose -f docker-compose-local.yaml up -d --build
if errorlevel 1 (
    echo EROARE: build-ul a esuat. Vezi logurile de mai sus.
    exit /b 1
)

start "" "http://localhost:%PORT%/conturi/inregistrare/"

echo.
echo Gata! PFASimplu ruleaza la http://localhost:%PORT%
echo   * Logarea este obligatorie: creeaza cont in pagina deschisa.
echo   * Datele sunt pe gazda, in %INSTALL_DIR%\src\dbsqlite\ (baza de date) si
echo     %INSTALL_DIR%\src\media\ (fisierele urcate/generate) -> fa backup la aceste foldere.
echo   * Oprire: docker compose -f docker-compose-local.yaml down
echo   * Loguri: docker compose -f docker-compose-local.yaml logs -f
echo   * Actualizare: ruleaza din nou acest script (face git pull + rebuild).
