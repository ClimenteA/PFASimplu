from django.urls import path
from .views import IncasariView, IncasariDescarcareView


urlpatterns = [
    path("", IncasariView.as_view(), name="incasari"),
    path("descarca/", IncasariDescarcareView.as_view(), name="descarca-incasari")
]
