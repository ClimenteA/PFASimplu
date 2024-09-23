from django.urls import path
from . import views


urlpatterns = [
    path("", views.RegistreView.as_view(), name="registre"),
    path("descarca-rjip/", views.RegistruJurnalDescarcaView.as_view(), name="descarca-registru-jurnal"),
    path("descarca-ref/", views.RegistruFiscalDescarcaView.as_view(), name="descarca-registru-fiscal"),
    path("descarca-inv/", views.RegistruInventarDescarcaView.as_view(), name="descarca-registru-inventar")
]

