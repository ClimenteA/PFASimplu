from django.urls import path
from .views import (
    SetariView,
    SetariViewDropData,
    SetariViewDownloadData,
    SetariIbanTrezorerieView,
)


urlpatterns = [
    path("", SetariView.as_view(), name="setari"),
    path("drop-data/", SetariViewDropData.as_view(), name="setari-drop-data"),
    path("download-data/", SetariViewDownloadData.as_view(), name="download-data"),
    path("iban-trezorerie/", SetariIbanTrezorerieView.as_view(), name="setari-iban-trezorerie"),
]
