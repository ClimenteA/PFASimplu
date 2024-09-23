from django.urls import path
from .views import SetariView, SetariViewDropData, ImportV1View


urlpatterns = [
    path("", SetariView.as_view(), name="setari"),
    path("drop-data/", SetariViewDropData.as_view(), name="setari-drop-data"),
    path("import-v1/", ImportV1View.as_view(), name="setari-import-v1"),
]
