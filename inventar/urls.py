from django.urls import path
from .views import InventarView, InventarDescarcaFisierView


urlpatterns = [
    path("", InventarView.as_view(), name="inventar"),
    path(
        "descarca-fisier-inventar/",
        InventarDescarcaFisierView.as_view(),
        name="descarca-fisier-inventar",
    ),
]
