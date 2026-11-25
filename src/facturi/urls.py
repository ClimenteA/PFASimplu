from django.urls import path
from .views import FacturiView, FacturiDescarcareView, FacturiSearchClientName

urlpatterns = [
    path("", FacturiView.as_view(), name="facturi"),
    path("descarca/", FacturiDescarcareView.as_view(), name="descarca-facturi"),
    path("search/<str:client_name>", FacturiSearchClientName.as_view(), name="search-client-name")
]
