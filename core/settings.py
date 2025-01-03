import os
import json
import shutil
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = "aplicatie-desktop-nu-conteaza-secret-trebuie-sa-fie-peste-50-de-caractere-sa-fie-considerata-sigura"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ["*"]

# Desktop app doesn't need SSL
# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SECURE = False
# SECURE_HSTS_SECONDS = 3600
# SECURE_HSTS_PRELOAD = False
# SECURE_SSL_REDIRECT = False
# SECURE_HSTS_INCLUDE_SUBDOMAINS = False


# Application definition

INSTALLED_APPS = [
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
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]


INTERNAL_IPS = [
    "127.0.0.1", "localhost"
]

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
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DB_DIR = os.path.join(BASE_DIR, "dbsqlite")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DB_DIR, "stocare.db"),
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
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

def get_font_path():

    development_path = os.path.join(static_files_path, "arial-font")
    if os.path.exists(development_path):
        return development_path
    
    pyinstaller_path = os.path.join(BASE_DIR, "_internal", "static", "arial-font")
    return pyinstaller_path


def get_current_version():

    versiune_path = os.path.join(static_files_path, "versiune.txt")
    if not os.path.exists(versiune_path):
        versiune_path = os.path.join(BASE_DIR, "_internal", "static", "versiune.txt")

    with open(versiune_path, "r") as f:
        ver = f.read().strip()

    return ver


def get_salarii_minim_brut_local():

    filepath = os.path.join(static_files_path, "minim_brut_an_val.json")
    if not os.path.exists(filepath):
        filepath = os.path.join(BASE_DIR, "_internal", "static", "minim_brut_an_val.json")

    with open(filepath, "r") as f:
        data = json.load(f)

    data = {int(k): v for k, v in data.items()}

    return data



MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

def make_media_dir():
    if not os.path.exists(MEDIA_ROOT):
        os.makedirs(MEDIA_ROOT)

make_media_dir()


def get_media_path():

    development_path = os.path.join(MEDIA_ROOT)
    if os.path.exists(development_path):
        return development_path
    
    pyinstaller_path = os.path.join(BASE_DIR, "_internal", "media")
    return pyinstaller_path


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
