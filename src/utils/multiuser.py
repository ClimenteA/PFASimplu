"""Izolarea datelor per utilizator (modul multi-user, pentru server/VPS).

Implicit aplicatia ruleaza ca aplicatie desktop, fara login
(PFASIMPLU_MULTI_USER=0). Cand PFASIMPLU_MULTI_USER=1:
- toate paginile cer autentificare (mai putin login/inregistrare);
- fiecare model de date are un camp `user`, iar managerul implicit
  filtreaza automat dupa utilizatorul cererii curente;
- fisierele urcate/generate se salveaza in media/user_<id>/ si pot fi
  descarcate doar de proprietar.

Utilizatorul curent este tinut intr-un ContextVar setat de middleware,
ca sa fie disponibil si in codul din utils/ care nu primeste `request`
(ex. get_save_path, get_extracts_path, calculele din modele).
"""

from contextvars import ContextVar

from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware  # noqa: F401 (ordine middleware)
from django.shortcuts import redirect
from django.urls import reverse

_current_user = ContextVar("pfasimplu_current_user", default=None)


def get_current_user():
    """Utilizatorul autentificat al cererii curente (sau None)."""
    return _current_user.get()


def multiuser_context(request):
    """Context pentru template-uri: modul multi-user activ sau nu."""
    return {
        "multi_user": settings.MULTI_USER,
        "allow_registration": settings.ALLOW_REGISTRATION,
    }


def get_user_media_prefix() -> str:
    """Prefixul folderului media al utilizatorului curent: 'user_<id>/' in
    modul multi-user, '' in modul desktop (fara login)."""
    if not settings.MULTI_USER:
        return ""
    user = get_current_user()
    if user is None:
        return ""
    return f"user_{user.id}/"


# Cai accesibile fara autentificare in modul multi-user.
def _cai_publice() -> tuple[str, ...]:
    return (
        settings.LOGIN_URL,
        reverse("inregistrare"),
        "/static/",
        "/admin/login/",
        "/__reload__/",
    )


class MultiUserMiddleware:
    """Seteaza utilizatorul curent pentru izolarea datelor si cere
    autentificare pe toate paginile cand PFASIMPLU_MULTI_USER=1.
    In modul desktop (implicit) nu face nimic.

    Trebuie plasat dupa django.contrib.auth.middleware.AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.MULTI_USER:
            return self.get_response(request)

        user = request.user if request.user.is_authenticated else None
        token = _current_user.set(user)
        try:
            if user is None:
                path = request.path
                if not any(path.startswith(cale) for cale in _cai_publice()):
                    login_url = f"{settings.LOGIN_URL}?next={request.get_full_path()}"
                    return redirect(login_url)
            return self.get_response(request)
        finally:
            _current_user.reset(token)
