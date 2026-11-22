from django.urls import path
from .views import DocumenteView, TVAGenereazaView, TVAMarcheazaPlatitaView


urlpatterns = [
    path("", DocumenteView.as_view(), name="documente"),
    path("tva/genereaza/", TVAGenereazaView.as_view(), name="tva-genereaza"),
    path("tva/marcheaza-platita/", TVAMarcheazaPlatitaView.as_view(), name="tva-marcheaza-platita"),
]
