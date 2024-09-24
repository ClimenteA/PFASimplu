from .settings import MEDIA_URL, MEDIA_ROOT
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static


urlpatterns = [
    path("", include("registre.urls")),
    path("cheltuieli/", include("cheltuieli.urls")),
    path("documente/", include("documente.urls")),
    path("facturi/", include("facturi.urls")),
    path("incasari/", include("incasari.urls")),
    path("inventar/", include("inventar.urls")),
    path("registre/", include("registre.urls")),
    path("setari/", include("setari.urls")),
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
