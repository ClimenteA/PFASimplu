from django.urls import path
from .views import InventarView

urlpatterns = [path("", InventarView.as_view(), name="inventar")]
