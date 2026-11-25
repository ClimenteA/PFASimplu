from django.urls import path

from .views import IncasariDescarcareView, IncasariView

urlpatterns = [
    path("", IncasariView.as_view(), name="incasari"),
    path("descarca/", IncasariDescarcareView.as_view(), name="descarca-incasari"),
]
