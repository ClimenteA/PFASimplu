#!/bin/sh
set -e

# Migrarile sunt versionate in git; la pornire doar le aplicam.
python manage.py migrate --noinput

# Static files pentru whitenoise (si pentru Caddy, daca le serveste el).
python manage.py collectstatic --noinput

# Cont de admin optional, din variabilele de mediu (idempotent).
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py shell -c "
from django.contrib.auth.models import User
import os
email = os.environ['DJANGO_SUPERUSER_EMAIL'].strip().lower()
if not User.objects.filter(username=email).exists():
    User.objects.create_superuser(email, email, os.environ['DJANGO_SUPERUSER_PASSWORD'])
    print('Superuser creat:', email)
"
fi

exec "$@"
