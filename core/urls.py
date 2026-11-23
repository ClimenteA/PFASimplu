from .settings import MEDIA_URL
from django.contrib import admin
from django.urls import path, include, re_path
from utils.files import media_serve_view


urlpatterns = [
    path("", include("registre.urls")),
    path("conturi/", include("conturi.urls")),
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

# In modul multi-user fisierele media sunt servite doar proprietarului
# (vezi utils.files.media_serve_view); in modul desktop ca pana acum.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_serve_view),
]
