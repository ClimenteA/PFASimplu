from django.urls import path
from .views import LoginView, InregistrareView, LogoutView


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("inregistrare/", InregistrareView.as_view(), name="inregistrare"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
