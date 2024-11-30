from django.urls import path
from .views import SetariView, SetariViewDropData, ImportV1View, ImportV2View, ImportFromPathV2View, SetariViewDownloadData


urlpatterns = [
    path("", SetariView.as_view(), name="setari"),
    path("drop-data/", SetariViewDropData.as_view(), name="setari-drop-data"),
    path("import-v1/", ImportV1View.as_view(), name="setari-import-v1"),
    path("import-v2/", ImportV2View.as_view(), name="setari-import-v2"),
    path("import-from-path-v2/", ImportFromPathV2View.as_view(), name="setari-import-from-path-v2"),
    path("download-data/", SetariViewDownloadData.as_view(), name="download-data"),
]
