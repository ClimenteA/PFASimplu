import os

from django.forms import ClearableFileInput


class _NumeFisier:
    """Valoarea afisata de widget: pastreaza linkul, dar taie folderul user_N/."""

    def __init__(self, fisier):
        self.fisier = fisier

    @property
    def url(self):
        return self.fisier.url

    def __str__(self):
        return os.path.basename(self.fisier.name)


class NumeFisierFileInput(ClearableFileInput):
    """FileField care afiseaza doar numele fisierului, fara folderul user_N/."""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context["widget"]["is_initial"]:
            context["widget"]["value"] = _NumeFisier(context["widget"]["value"])
        return context
