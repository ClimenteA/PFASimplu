from django.urls import path
from .views import DocumenteView


urlpatterns = [
    path("", DocumenteView.as_view(), name="documente")
]

