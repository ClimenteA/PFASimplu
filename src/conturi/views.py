from django.conf import settings
from django.contrib.auth import login, logout
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .forms import EmailAuthenticationForm, EmailUserCreationForm


def _next_sigur(request, fallback="/"):
    """URL-ul `next` doar daca pointeaza spre aceeasi gazda (anti open-redirect)."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return fallback


class LoginView(View):
    """Login cu email + parola, pe formularul de autentificare din Django."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(_next_sigur(request))
        return render(request, "conturi/login.html", {
            "form": EmailAuthenticationForm(request),
            "next": request.GET.get("next", ""),
        })

    def post(self, request):
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(_next_sigur(request))
        return render(request, "conturi/login.html", {
            "form": form,
            "next": request.POST.get("next", ""),
        })


class InregistrareView(View):
    """Inregistrare cu email + parola, pe UserCreationForm din Django
    (validari de parola incluse: lungime, parole comune, doar cifre etc.).
    Se poate bloca de pe server cu PFASIMPLU_ALLOW_REGISTRATION=0."""

    def get(self, request):
        if not settings.ALLOW_REGISTRATION:
            raise Http404()
        if request.user.is_authenticated:
            return redirect("/")
        return render(request, "conturi/inregistrare.html", {"form": EmailUserCreationForm()})

    def post(self, request):
        if not settings.ALLOW_REGISTRATION:
            raise Http404()
        form = EmailUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
        return render(request, "conturi/inregistrare.html", {"form": form})


class LogoutView(View):

    def post(self, request):
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)
