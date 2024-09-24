# PFASimplu V2 in progress


# Instalare pt. developeri

Aplicatia este facuta in Python, Django cu SQLiteDB. 

- clone repo;
- `virtualenv .venv`;
- `source .venv/bin/activate`;
- `pip install -r requirements.txt`;
- `python manage.py makemigrations`;
- `python manage.py migrate`;
- `make migrate-all` - pt. Ubuntu pentru a face toate migrarile;
- `make run` - pt. a porni Django dev. server (aka `python manage.py runserver`);
- `purge-db` - pt. a sterge `stocare.db` (sqlite db) si toate folderele `migrations`;

Windows:

```shell
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" --icon=app.ico gui.py
```

Linux:

```shell
pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" --icon=app.ico gui.py
```

```shell
pyinstaller --windowed --onefile --add-data "templates:templates" --add-data "static:static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload gui.py
```

```shell
pyinstaller --windowed --onefile --add-data "templates:templates" --add-data "static:static" --collect-all django_cleanup --collect-all whitenoise --collect-all matplotlib --collect-all django_browser_reload gui.py
```


<!-- 
- https://blog.factureaza.ro/campurile-obligatorii-e-factura/
- https://mfinante.gov.ro/web/efactura/aplicatii-web-ro-efactura
- https://www.anaf.ro/CompletareFacturaSimplificat/faces/factura/informatiigenerale.xhtml
- https://mfinante.gov.ro/ro/web/efactura/informatii-tehnice
- https://mfinante.gov.ro/static/10/Mfp/Ghide-Factura_21022024.pdf
- https://mfinante.gov.ro/static/10/eFactura/PrezentareE-factura.pdf
- https://mfinante.gov.ro/apps/agenticod.html?pagina=domenii -->
