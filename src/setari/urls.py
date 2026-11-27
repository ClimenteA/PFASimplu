from django.urls import path

from .views import (
    SetariActualizeazaView,
    SetariIbanTrezorerieView,
    SetariView,
    SetariViewDownloadData,
    SetariViewDropData,
)

urlpatterns = [
    path("", SetariView.as_view(), name="setari"),
    path(
        "actualizeaza/",
        SetariActualizeazaView.as_view(),
        name="setari-actualizeaza",
    ),
    path("drop-data/", SetariViewDropData.as_view(), name="setari-drop-data"),
    path("download-data/", SetariViewDownloadData.as_view(), name="download-data"),
    path(
        "iban-trezorerie/",
        SetariIbanTrezorerieView.as_view(),
        name="setari-iban-trezorerie",
    ),
]
