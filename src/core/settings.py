import json
import os
import shutil
from pathlib import Path

# BASE_DIR = radacina surselor (src/), care contine app-urile, templates/,
# static/, media/ si dbsqlite/. PROJECT_ROOT = radacina repo-ului, unde sta
# pyproject.toml.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


def _get_app_version() -> str:
    """Versiunea aplicatiei, citita din pyproject.toml (sursa unica de adevar)."""
    import tomllib

    for pyproject in (BASE_DIR / "pyproject.toml", PROJECT_ROOT / "pyproject.toml"):
        try:
            with open(pyproject, "rb") as f:
                return tomllib.load(f)["project"]["version"]
        except (OSError, KeyError, tomllib.TOMLDecodeError):
            continue
    return ""


APP_VERSION = _get_app_version()

# Versiunea anunțată ca disponibilă, afișată în footerul paginii Setări.
# Se actualizează manual când se publică un release pe GitHub (cache-ul
# HTTP al interogării către pyproject.toml putea afișa o versiune veche).
AVAILABLE_APP_VERSION = "3.0.1"
GITHUB_REPO_URL = "https://github.com/ClimenteA/PFASimplu"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/


def _env_bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


# Permite crearea de conturi noi din pagina de inregistrare. Implicit 1;
# seteaza PFASIMPLU_ALLOW_REGISTRATION=0 pe server pentru a bloca
# inregistrările (utilizatorii existenti se pot autentifica in continuare).
ALLOW_REGISTRATION = _env_bool("PFASIMPLU_ALLOW_REGISTRATION", "1")

# SECURITY WARNING: keep the secret key used in production secret!
# Pe server se seteaza PFASIMPLU_SECRET_KEY in .env.prod.
SECRET_KEY = os.environ.get("PFASIMPLU_SECRET_KEY") or (
    "doar-pentru-dezvoltare-schimba-valoarea-asta-in-productie-prin-PFASIMPLU_SECRET_KEY"
)

# SECURITY WARNING: don't run with debug turned on in production!
# Implicit DEBUG=1 in dezvoltare (ca Django sa serveasca fisierele statice).
# In Docker se seteaza explicit PFASIMPLU_DEBUG=0.
DEBUG = _env_bool("PFASIMPLU_DEBUG", "1")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("PFASIMPLU_ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]

# Ex. PFASIMPLU_CSRF_TRUSTED_ORIGINS=https://pfa.exemplu.ro
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("PFASIMPLU_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# In productie (DEBUG=0), aplicatia sta in spatele unui proxy TLS (Caddy).
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookie-urile "Secure" presupun HTTPS. Varianta Docker locala ruleaza pe
# http://localhost, deci le dezactiveaza prin PFASIMPLU_SECURE_COOKIES=0
# (altfel sesiunea de login nu este trimisa de browser).
SECURE_COOKIES = _env_bool("PFASIMPLU_SECURE_COOKIES", "0" if DEBUG else "1")
if SECURE_COOKIES:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


# Application definition

INSTALLED_APPS = [
    "utils",
    "conturi",
    "cheltuieli",
    "documente",
    "facturi",
    "incasari",
    "inventar",
    "registre",
    "setari",
    "django_browser_reload",
    "django_cleanup.apps.CleanupConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "utils.multiuser.MultiUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]


INTERNAL_IPS = ["127.0.0.1", "localhost"]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "utils.multiuser.multiuser_context",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DB_DIR = os.environ.get("PFASIMPLU_DB_DIR") or os.path.join(BASE_DIR, "dbsqlite")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # Testele end-to-end (folderul tests/) pot redirectiona baza de date
        # printr-o variabila de mediu, ca sa nu atinga datele reale.
        "NAME": os.environ.get("PFASIMPLU_DB_PATH")
        or os.path.join(DB_DIR, "stocare.db"),
    },
    "OPTIONS": {
        "timeout": 20,
        "transaction_mode": "IMMEDIATE",
        "init_command": "PRAGMA synchronous=3; PRAGMA cache_size=2000;",
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Bucharest"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

static_files_path = os.path.join(BASE_DIR, "static")

STATIC_URL = "static/"
STATICFILES_DIRS = [static_files_path]
# In Docker fisierele statice se scriu in /app/staticfiles (volum montat),
# deci radacina poate fi suprascrisa prin variabila de mediu.
STATIC_ROOT = os.environ.get("PFASIMPLU_STATIC_ROOT") or os.path.join(
    BASE_DIR, "staticfiles"
)


def get_font_path():
    return os.path.join(static_files_path, "arial-font")


def get_salarii_minim_brut_local():
    filepath = os.path.join(static_files_path, "minim_brut_an_val.json")
    with open(filepath, "r") as f:
        data = json.load(f)

    data = {int(k): v for k, v in data.items()}

    return data


MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("PFASIMPLU_MEDIA_ROOT") or os.path.join(BASE_DIR, "media")


def make_media_dir():
    if not os.path.exists(MEDIA_ROOT):
        os.makedirs(MEDIA_ROOT)


make_media_dir()


def get_media_path():
    """Folderul media al utilizatorului curent: media/user_<id>/.
    Fara utilizator in context (comenzi de management) ramane media/."""
    from utils.multiuser import get_user_media_prefix

    prefix = get_user_media_prefix()
    development_path = os.path.join(MEDIA_ROOT, prefix)
    os.makedirs(development_path, exist_ok=True)
    return development_path


def get_extracts_path(extra_dir: str | None = None):
    extracts_path = os.path.join(get_media_path(), "extracts")
    if extra_dir:
        extracts_path = os.path.join(extracts_path, extra_dir)
        shutil.rmtree(extracts_path, ignore_errors=True)
    os.makedirs(extracts_path, exist_ok=True)
    return extracts_path


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Autentificare (obligatorie; toate paginile cer login).
LOGIN_URL = "/conturi/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/conturi/login/"

# Static files: whitenoise comprimat in modul server (DEBUG=0).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}
