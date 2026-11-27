from django.urls import path

from .views import IncasariDescarcareView, IncasariUEDescarcaView, IncasariView

urlpatterns = [
    path("", IncasariView.as_view(), name="incasari"),
    path("descarca/", IncasariDescarcareView.as_view(), name="descarca-incasari"),
    path(
        "ue/descarca/",
        IncasariUEDescarcaView.as_view(),
        name="incasari-ue-descarca",
    ),
]
