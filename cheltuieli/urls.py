from django.urls import path
from .views import CheltuieliView, CheltuieliDescarcareView, CheltuieliSearchFurnizor


urlpatterns = [
    path("", CheltuieliView.as_view(), name="cheltuieli"),
    path("descarca/", CheltuieliDescarcareView.as_view(), name="descarca-cheltuieli"),
    path("cauta-furnizor/<str:nume_furnizor>/", CheltuieliSearchFurnizor.as_view(), name="cheltuieli-cauta-furnizor"),
]
