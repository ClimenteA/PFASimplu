from django.urls import path

from .views import (
    CheltuieliDescarcareView,
    CheltuieliSearchFurnizor,
    CheltuieliTVADescarcaView,
    CheltuieliView,
)

urlpatterns = [
    path("", CheltuieliView.as_view(), name="cheltuieli"),
    path("descarca/", CheltuieliDescarcareView.as_view(), name="descarca-cheltuieli"),
    path(
        "tva/descarca/",
        CheltuieliTVADescarcaView.as_view(),
        name="cheltuieli-tva-descarca",
    ),
    path(
        "cauta-furnizor/<str:nume_furnizor>/",
        CheltuieliSearchFurnizor.as_view(),
        name="cheltuieli-cauta-furnizor",
    ),
]
