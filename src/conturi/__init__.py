"""Conturi de utilizator pentru modul multi-user (server/VPS).

Foloseste sistemul de autentificare inclus in Django (django.contrib.auth):
login cu email + parola si inregistrare. In modul desktop
(PFASIMPLU_MULTI_USER=0, implicit) paginile acestea redirectioneaza spre
aplicatie - nu exista login in aplicatia desktop.
"""
