from django.urls import path
from .views import CheltuieliView, CheltuieliDescarcareView


urlpatterns = [
    path("", CheltuieliView.as_view(), name="cheltuieli"),
    path("descarca/", CheltuieliDescarcareView.as_view(), name="descarca-cheltuieli")
]
