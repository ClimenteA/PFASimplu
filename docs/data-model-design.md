# PFASimplu — redesignul modelului de date

> **Status: propunere, nu implementare.** Acest document nu modifica niciun fisier din aplicatie.
> Scopul: un schema "curat" care sa inlocuiasca modelele actuale intr-o baza de date noua
> (fara migrari de date), pastrand comportamentul vizibil al aplicatiei.

---

## 1. Rezumat executiv

Da, modelele pot fi simplificate semnificativ. Cel mai mare castig nu vine din
normalizarea clasica (chei straine peste tot), ci din trei lucruri:

1. **O singura sursa de adevar pentru fiecare fapt.** In prezent ~20 de coloane
   sunt recalculate la fiecare `save()` din alte coloane (`suma_in_ron`,
   `deducere_in_ron`, tot blocul de amortizare, `curs_bnr_aplicat`,
   `baza_in_lei`, `tva_autolichidata`, `mijloc_fix`, `obiect_de_inventar`,
   `tip_achizitie`, `scos_din_uz`). Ele pot deveni `@property` / functii pure.
2. **Inlocuirea celor doua `JSONField` care functioneaza ca mini-tabele** cu
   modele copil reale: liniile facturii si conturile bancare.
3. **Scoaterea datelor structurate din text liber** (`DocumenteModel.mentiuni`
   contine `Plata spv 123,45 RON`, parsat prin regex in doua locuri) si
   corectarea tipurilor de campuri (date stocate ca `DateTimeField`, an stocat
   ca `IntegerField` desi utilizatorul introduce o data, booleeni nullable).

Dimensiunea problemei: `CheltuialaModel` are **36 de campuri concrete**;
dintre acestea **~17 sunt pur derivate**. Schema propusa il aduce la **~21 de
campuri**, cu aceleasi valori disponibile ca proprietati. `FacturaModel`
pierde un JSON de 7 chei in favoarea unui tabel `LinieFactura`, iar
`SetariModel` pierde 5 coloane CAEN + IBAN-ul duplicat + JSON-ul de conturi.

---

## 2. Starea actuala (pe scurt)

| Model | Campuri concrete | Rol |
|---|---|---|
| `utils.UserOwnedModel` (abstract) | `user` | izolare multi-user; in desktop e `NULL` |
| `utils.CommonIncasariCheltuieliModel` (abstract) | `suma_in_ron`, `suma`, `valuta`, `tip_tranzactie`, `data_inserarii`, `fisier`, `actualizat_la` | baza pentru incasari si cheltuieli |
| `incasari.IncasariModel` | + `sursa_venit`, `factura` (O2O) | incasari; `data_inserarii IS NULL` inseamna "neincasata" |
| `cheltuieli.CheltuialaModel` | + 28 | cheltuieli, deductibilitate, amortizare, taxare inversa |
| `facturi.FacturaModel` | 19 | facturi emise; linii in `JSONField`; PDF/XML generate in `save()` |
| `setari.SetariModel` | 19 | date PFA, IBANuri (JSON + coloana legacy), CAEN 1..5 |
| `setari.McpApiKey` | 7 | chei API hash-uite |
| `documente.DocumenteModel` | 7 | arhiva ANAF; tip/an/suma parsate din PDF in `mentiuni` |
| `inventar`, `registre` | 0 | doar view-uri; `registre` e montat de doua ori in URL-uri |

Fluxul real al datelor:

```
Setari (singleton prin objects.first())
  ├──> FacturaModel.save()  -> PDF + XML (foloseste Setari + conturile IBAN)
  │        └──> IncasariModel.factura (OneToOne) -> PDF-ul copiat in incasare
  ├──> CheltuialaModel.save() -> suma_in_ron, deducere_in_ron, amortizare, TVA inversa
  │        └──> utils/tva.py (D301/D390 + jurnal) citeste valorile derivate stocate
  ├──> DocumenteModel.save() -> parseaza PDF-ul si rescrie tip/an/mentiuni
  └──> registre/views.py + setari/views.py (export anual) -> agregari SQL pe coloane derivate
```

---

## 3. Probleme gasite (cu prioritati)

### P1 — Valori derivate stocate ca si coloane (prioritate mare)

Toate sunt scrise in `save()` si nu pot fi modificate de utilizator (exceptie
`ani_amortizare`), dar sunt sursa de adevar pentru rapoarte:

| Camp | Sursa de adevar | Unde se recalculeaza |
|---|---|---|
| `suma_in_ron` | `suma` + `valuta` + `data_inserarii` | `utils/models.py:70-76` (BNR) |
| `deducere_in_ron` | `deductibila` + `suma_in_ron` + alte cheltuieli din an + TVA inversa | `cheltuieli/models.py:326-517` |
| `curs_bnr_aplicat`, `baza_in_lei`, `tva_autolichidata` | `furnizor_tara`, `valuta`, `data_facturii`, `suma` | `cheltuieli/models.py:154-210` |
| `mijloc_fix`, `obiect_de_inventar` | `deductibila` | `cheltuieli/models.py:339,357` |
| `grupa`, `durata_normala_de_functionare` | `cod_de_clasificare` (catalog) | `cheltuieli/models.py:358-360` |
| `anul/luna_darii_in_folosinta`, `anul/luna_amortizarii_complete` | `data_punerii_in_functiune`, `data_amortizarii_complete` | `cheltuieli/models.py:361-383` |
| `data_inceperii_amortizarii`, `data_amortizarii_complete`, `amortizare_lunara`, `cota_de_amortizare` | `cod_de_clasificare` + `ani_amortizare` + `suma_in_ron` | `cheltuieli/models.py:369-380` |
| `tip_achizitie` | `furnizor_tara` | `cheltuieli/models.py:172-177` |
| `scos_din_uz` | `data_iesirii_din_uz` | `inventar/views.py:99` |

Consecinte:
- Ordinea apelurilor din `save()` conteaza (taxarea inversa inainte de
  conversie, comentariu la `cheltuieli/models.py:320`), deci valorile pot
  divergea daca o ruta ocoleste `save()` (exact ce face e2e-ul la
  `tests/test_an_complet.py:820-824` prin SQL direct).
- `grupa`, `durata_normala_de_functionare`, `cota_de_amortizare` si cele 4
  campuri an/luna sunt citite **o singura data** in tot codul de productie:
  in `utils/mijloc_fix_pdf.py:46-53`. 6 coloane pentru o singura fisa PDF.
- `curs_bnr_aplicat` e rescris la fiecare salvare chiar daca utilizatorul il
  seteaza manual (test la `documente/tests.py:174-180`) — o coloana care
  minte pe utilizator.

### P2 — JSON ca baza de date mini-table (prioritate mare)

- `FacturaModel.produse_sau_servicii` (`JSONField(default=list)`): 7 chei per
  linie, validare doar in JavaScript (`templates/facturi.html:266-271`),
  fara schema in model. Citit la generarea PDF/XML
  (`facturi/models.py:446-455`, `templates/efactura.xml:87-105`) si exportat
  ca string in CSV/XLSX (`utils/views.py:140-147`).
- `SetariModel.conturi_iban` (`JSONField`): lista de
  `{"valuta", "iban"}`, cu unicitate per valuta validata doar in
  `setari/forms.py:68-91`. In plus, `SetariModel.iban` (coloana legacy) e
  sincronizat doar in `SetariForm.clean()` (`setari/forms.py:93-104`);
  orice scriere prin ORM/MCP (ex. `mcp_server/tools.py:122`) il lasa stale.

### P3 — Date structurate in text (prioritate medie)

`DocumenteModel.mentiuni` contine, printre altele, `Plata spv 123,45 RON`.
Aceeasi regex `Plata spv ([\d.,]+) RON` e duplicata in
`documente/models.py:126` si `setari/views.py:437`. `parse_tip_document`
decide in `save()` daca are loc o parsare de PDF, cu **doua apeluri
`super().save()`** (`documente/models.py:136,154,176`) si exceptii inghitite.

### P4 — Tipuri si enumerari inconsistente (prioritate medie)

- `FacturaModel.data_emitere` / `data_scadenta` sunt `DateTimeField`, dar
  codul le foloseste doar ca date (`.date()` la `facturi/models.py:423-424`,
  widget `type="date"`).
- `facturi.ModalitatePlata` foloseste codurile `"42"` / `"10"`, in timp ce
  `utils.TipTranzactie` foloseste `"BANCAR"` / `"NUMERAR"` pentru aceeasi
  conceptie (`incasari/views.py:47-50` face traducerea manual).
- `DocumenteModel.document_pentru_anul` e `IntegerField`, dar formularul
  afiseaza un `DateField` si ii taie luna/ziua (`documente/forms.py:11-33`).
- Booleeni nullable cu default: `scutit_cas/cass/impozit`, `mijloc_fix`,
  `obiect_de_inventar`, `scos_din_uz`, `parse_tip_document`.
- Valori de choice lungi, in romana, ajung in baza si in exporturi
  (`SursaVenit` are o valoare de 170+ caractere); cazul special
  `"Mijloc fix peste 2500 RON"` cu eticheta `"peste 5000 RON"`
  (`cheltuieli/models.py:39-42`) e o consecinta directa a faptului ca
  valorile vechi nu au putut fi schimbate. Baza noua elimina constrangerea.
- `nume_cheltuiala = CharField(10000)`, `FileField(max_length=100000)`,
  `mentiuni = TextField(50000)`, `tip_factura = CharField(300)`.

### P5 — Semantică dubla / pierduta (prioritate medie)

`IncasariModel.data_inserarii` inseamna simultan "data tranzactiei" si
"e incasata?" (`NULL` = in asteptare). In acelasi timp, "factura incasata" e
data de relatia `IncasariModel.factura` (O2O), iar "facturi neincasate" din
dashboard e calculata din `data_inserarii__isnull=True`. Doua concepte
diferente cu acelasi nume; factura emisa fara incasare nu apare in
"neincasate".

### P6 — Efecte secundare in `save()` (prioritate scazuta, dar de rezolvat)

- `FacturaModel.save()` (`facturi/models.py:403-470`) regenereaza PDF-ul (si
  XML-ul) la **fiecare** salvare, folosind un fisier tmp cu nume fix.
- `SetariView.post` sterge toate randurile `SetariModel` si le resalveaza
  (`setari/views.py:183`) pentru a simula singletonul.
- `CODURI_CLASIFICARE` (~3000 de linii) sta in `cheltuieli/models.py:532+`,
  desi e date de referinta, nu model.

---

## 4. Schema propusa

Principii:

* **O singura sursa de adevar**: utilizatorul introduce faptele (sume, date,
  optiuni); tot restul se calculeaza.
* **Calcul determinist, intr-un singur loc**: functii pure in `*/calcul.py` /
  `*/services.py`, apelate atat din view-uri cat si din teste.
* **Pastrarea API-ului de citire**: valorile derivate raman disponibile ca
  `@property` cu aceleasi nume, deci template-urile, MCP-ul si majoritatea
  codului de raportare nu se schimba. Se schimba doar interogarile ORM care
  filtreaza/agreaza pe ele.
* **Fara migrari de date**: se regenereaza `0001_initial.py` dupa model.

### 4.1 `utils/models.py` — baza

```python
class UserOwnedModel(models.Model):          # neschimbat
    user = ForeignKey(..., null=True, blank=True, on_delete=CASCADE)
    objects = UserScopedManager()

class TranzactieModel(UserOwnedModel):       # renume sugerat; vezi nota
    suma = DecimalField(max_digits=14, decimal_places=4)
    valuta = CharField(max_length=3, choices=Valuta, default=Valuta.RON)
    tip_tranzactie = CharField(max_length=10, choices=TipTranzactie, default=BANCAR)
    data_inserarii = DateField(...)          # data operatiunii; se pastreaza numele
    fisier = FileField(...)
    actualizat_la = DateTimeField(auto_now=True)

    @property
    def suma_in_ron(self) -> Decimal:
        return to_ron(self.suma, self.valuta, self.data_inserarii)
```

> Numele `data_inserarii` e pastrat pentru a limita diff-ul, desi reprezinta
> data operatiunii, nu data introducerii in aplicatie (vezi D6).

`suma_in_ron` dispare din baza. `to_ron` e deja `@lru_cache`
(`utils/valuta.py:51-59`); pentru determinism propun un mic tabel
`CursBnr(data, valuta, curs)` cu incarcare lazy (o singura interactiune cu
`cursvalutarbnr` per zi+valuta). Astfel rapoartele pentru ani vechi nu mai
depind de retea si valorile nu se schimba intre rulari.

> Nota: numele clasei `TranzactieModel` si al campului `data_inserarii` sunt
> sugestii; pentru un diff minim se poate pastra
> `CommonIncasariCheltuieliModel` si numele `data_inserarii`, schimband doar
> tipul in `DateField`. Numele actual e insa misleading (e data operatiunii,
> nu a inserarii in aplicatie).

### 4.2 `cheltuieli/models.py`

**Campuri ramase in baza (21, față de 36):**

`id`, `user`, `nume_cheltuiala`, `suma`, `valuta`, `tip_tranzactie`,
`data_inserarii`, `fisier`, `actualizat_la`, `deductibila`,
`cod_de_clasificare`, `ani_amortizare`, `data_punerii_in_functiune`,
`data_iesirii_din_uz`, `modalitate_iesire_din_uz`,
`document_justificativ_iesire_din_uz`, `furnizor_denumire`,
`furnizor_cod_fiscal`, `furnizor_tara`, `numar_factura`, `data_facturii`.

**Proprietati (nu coloane):**
`suma_in_ron`, `deducere_in_ron`, `este_taxare_inversa`, `este_ue`,
`tip_achizitie` (derivat din `furnizor_tara` prin `este_tara_ue`),
`curs_bnr_aplicat`, `baza_in_lei`, `tva_autolichidata`,
`obiect_de_inventar`, `mijloc_fix`, `grupa`,
`durata_normala_de_functionare`, `data_inceperii_amortizarii`,
`data_amortizarii_complete`, `amortizare_lunara`, `cota_de_amortizare`,
`anul_darii_in_folosinta`, `luna_darii_in_folosinta`,
`anul_amortizarii_complete`, `luna_amortizarii_complete`, `scos_din_uz`.

**Cum se calculeaza `deducere_in_ron` fara coloana stocata**

Regulile cu plafoane anuale (protocol 2%, ajutoare 5% din salarii,
contributii 5% din brut, sport/pensie/asigurari/cotizatii in EUR) depind de
celelate cheltuieli din acelasi an. Solutia propusa e o functie pura care
face **o singura trecere** pe randurile anului:

```python
# cheltuieli/calcul.py
def calculeaza_deduceri_anului(an: int) -> dict[int, Decimal]:
    """{pk: deducere_in_ron} pentru toate cheltuielile anului, in ordinea
    (data_inserarii, id). Include regulile de cap si TVA-ul autolichidat."""
    ...

def cu_deduceri(qs):
    """Ataseaza valoarea calculata fiecarui obiect (pentru liste/exporturi)."""
    ...
```

* `CheltuialaModel.deducere_in_ron` apeleaza functia de mai sus cu un cache
  per cerere, cheiat pe `(an, count, max(id), max(actualizat_la))`.
* Validarea la salvare re-ruleaza calculul cu candidatul inclus si ridica
  `ValidationError` daca se depaseste un plafon (mesajele actuale raman).
* Rapoartele (`registre/views.py`, `setari/views.py`) apeleaza
  `calculeaza_deduceri_anului(an)` **o data** si folosesc dictionarul, in loc
  de ~11 `aggregate(Sum("deducere_in_ron"))` + 12 filter-blockuri.
* `get_total_cheltuieli(an)`, `get_total_cheltuieli_pe_luni(an)`,
  `luni_amortizare_active_in_an(an)` devin functii in acelasi modul.

**Catalogul**: `CODURI_CLASIFICARE` se muta in `cheltuieli/catalog.py`
(lista Python read-only; nu meritat tabel in baza). De acolo se deriva
`grupa`, `durata_normala_de_functionare`, `ani_amortizare` (fallback daca
utilizatorul nu il seteaza), `data_*amortizarii`, `amortizare_lunara`,
`cota_de_amortizare`.

**Enumuri**: `Deductibilitate` primeste coduri scurte si stabile
(`INTEGRAL`, `INVENTAR`, `MIJLOC_FIX`, `AUTO_50`, `SPORT`, `PENSIE_III`,
`ASIG_MED`, `PROTOCOL`, `SALARII`, `AJUTOARE`, `CONTRIB_OBLIG`,
`COTIZATII`), cu etichetele romanesti actuale in `label`. Fiind baza noua,
nu e nevoie de compatibilitate cu valorile vechi.

### 4.3 `facturi/models.py` + linii

```python
class FacturaModel(UserOwnedModel):
    serie, numar
    data_emitere = DateField(default=date.today)
    data_scadenta = DateField(...)
    tip_factura = CharField(max_length=30, choices=TipFactura, ...)
    nume, cif, nr_reg_com, localitate, adresa, email, telefon
    tip_tranzactie = CharField(choices=TipTranzactie, ...)   # unificat
    valuta = CharField(max_length=3, choices=Valuta, ...)
    nota = TextField(blank=True)
    fisier_efactura_xml, fisier_factura_pdf = FileField(...)

    @property
    def total_de_plata(self): return sum(l.subtotal for l in self.linii.all())

    @property
    def produse_sau_servicii(self):
        """Compatibil cu efactura.xml / creeaza_factura_pdf."""
        return [ {...} for l in self.linii.all() ]

class LinieFactura(models.Model):
    factura = ForeignKey(FacturaModel, related_name="linii", on_delete=CASCADE)
    nume = CharField(max_length=300)
    cod_unitate = CharField(max_length=10)
    cantitate = DecimalField(...)          # fost "numar_unitati"
    pret_unitar = DecimalField(...)        # fost "pret_pe_unitate"
    @property
    def subtotal(self): return rotund2(self.cantitate * self.pret_unitar)
```

* Generarea PDF/XML iese din `save()` intr-un serviciu
  `facturi/generare.py::genereaza_documente(factura)` apelat din
  `FacturiView.post` dupa validarea formularului. `save()` nu mai are efecte
  de scriere pe disc.
* `FacturaForm` pastreaza textarea-ul hidden JSON (deci e2e-ul si JS-ul
  Alpine raman), dar il valideaza (`list[dict]` cu cheile asteptate) si
  creeaza/actualizeaza `LinieFactura` intr-un `transaction.atomic` in
  `form.save()`. Alternativa (formset) e discutata la §6.

### 4.4 `setari/models.py`

```python
class SetariModel(UserOwnedModel):
    nume, localitate, adresa, nr_reg_com, cif, email, telefon
    caen_principal = CharField(max_length=4)
    caen_secondare = JSONField(default=list)   # 5 -> 1 camp, lista de stringuri
    scutit_cas/cass/impozit = BooleanField(default=False)
    cod_tva_intracomunitar, cont_iban_trezoreria
    actualizat_la = DateTimeField(auto_now=True)

    def get_iban_pentru_valuta(self, valuta=None):
        # RON -> orice cont -> None; nu mai exista fallback "iban legacy"

class ContBancar(models.Model):
    setari = ForeignKey(SetariModel, related_name="conturi", on_delete=CASCADE)
    valuta = CharField(max_length=3, choices=Valuta)
    iban = CharField(max_length=50, validators=[validate_iban_length])
    UniqueConstraint(fields=["setari", "valuta"])
```

* Se elimina `SetariModel.iban` (legacy) si `conturi_iban` (JSON).
* Unicitatea e in baza, nu doar in formular.
* Singletonul se rezolva prin `SetariModel.objects.get_or_create_for_user(user)`
  cu `UniqueConstraint` pe `user` (in desktop: o singura inregistrare cu
  `user IS NULL`), nu prin `delete()` + `save()`.
* UI: `inlineformset_factory` pentru conturi (4-5 randuri); daca se vrea diff
  minim, se poate pastra widgetul Alpine si se transforma JSON-ul in randuri
  in `SetariForm.save()`.

### 4.5 `documente/models.py`

```python
class DocumenteModel(UserOwnedModel):
    tip_document = CharField(max_length=30, choices=TipDocument)  # coduri scurte
    data_document = DateField(null=True, blank=True)   # inlocuieste anul intreg
    suma_plata = DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    mentiuni = TextField(blank=True)                  # doar note pentru om
    fisier = FileField(...)
    actualizat_la = DateTimeField(auto_now_add=True)

    @staticmethod
    def total_plati_la_stat():
        qs = DocumenteModel.objects.filter(
            tip_document=TipDocument.DOVADA_PLATA_TAXE_SI_IMPOZITE
        )
        return rotund2(D(qs.aggregate(total=Sum("suma_plata"))["total"] or 0))
```

* Parsarea PDF-ului se muta in `documente/services.py::parseaza_document(path)`
  care intoarce `{tip_document, data_document, suma_plata, mentiuni}`.
  View-ul o apeleaza inainte de `form.save()`; dispare `parse_tip_document`
  (devine parametru al formularului/serviciului, nu stare in baza) si
  dispare al doilea `super().save()`.
* Se elimina regexul duplicat din `setari/views.py:434-444`; ambele locuri
  folosesc `DocumenteModel.total_plati_la_stat()`.

### 4.6 `incasari/models.py`

```python
class IncasariModel(UserOwnedModel):
    sursa_venit = CharField(choices=SursaVenit, ...)   # coduri scurte
    suma, valuta, tip_tranzactie, fisier, actualizat_la, data_inserarii  # baza comuna
    data_incasarii = DateField(null=True, blank=True)  # NULL = in asteptare
    factura = OneToOneField(FacturaModel, null=True, on_delete=SET_NULL)

    @property
    def este_incasata(self): return self.data_incasarii is not None
```

* Se adauga campul explicit `data_incasarii` (nullable) langa `data_inserarii`
  (data operatiunii). Starea "in asteptare" e data de `data_incasarii IS NULL`,
  nu de `data_inserarii IS NULL`. Toate calculurile `get_total_incasari` /
  `get_total_neincasate` / `get_total_incasari_pe_luni` folosesc campul explicit.
* Relatia `factura` ramane, dar se adauga o metrica separata
  `facturi_fara_incasare` (`FacturaModel.objects.filter(incasare__isnull=True)`)
  in dashboard, ca sa nu se mai confunde cu "in asteptare".
* `suma_in_ron` devine proprietate (ca la cheltuieli).

### 4.7 `McpApiKey`

Neschimbat (deja stocheaza doar hash + salt). Singura ajustare: folosirea
managerului `objects` normal, nu a celui user-scoped, ceea ce e deja cazul.

---

## 5. Plan de implementare (baza noua)

1. **Pregatire (fara schimbare de comportament)**
   - Branch nou; se noteaza ca `dbsqlite/stocare.db` si `tests/.runtime/test.db`
     se pot sterge.
   - Se muta `CODURI_CLASIFICARE` in `cheltuieli/catalog.py`.
   - Se introduc modulele `cheltuieli/calcul.py`, `facturi/generare.py`,
     `documente/services.py` si `utils/curs_bnr.py` (tabel `CursBnr`).
2. **Schema noua**
   - Se rescriu modelele in ordinea: `utils` -> `incasari` -> `cheltuieli`
     -> `facturi` -> `setari` -> `documente`.
   - Se sterg toate `*/migrations/0001_initial.py` si se ruleaza:
     `python manage.py makemigrations cheltuieli documente facturi incasari setari`
     apoi `python manage.py migrate --noinput` pe o baza goala.
   - Nu se scriu migrari de date (nu exista date de pastrat).
3. **Adaptarea consumatorilor**
   - Formulare: `CheltuieliForm.exclude` se curata de campurile care nu mai
     exista; `SetariForm` se rescrie pentru formset/conturi; `DocumenteForm`
     foloseste `data_document` (noul nume al lui `document_pentru_anul`); `FacturaForm` valideaza liniile; `IncasariForm` include `data_incasarii`.
   - View-uri: agregarile ORM pe campuri derivate se inlocuiesc cu
     apeluri catre noile functii de calcul (`calculeaza_deduceri_anului`, `get_total_cheltuieli`, `get_total_cheltuieli_pe_luni` — vezi §4.2).
   - Template-uri: se actualizeaza numele campurilor (`data_incasarii`,
     `data_document`, `conturi`), se scoate selectul `tip_achizitie` daca se
     deriva din tara; cel putin 20 de referiri.
   - `mcp_server/tools.py`: se actualizeaza campurile returnate
     (`suma_in_ron` ca proprietate, `iban` eliminat, `conturi` din relatie,
     codurile scurte de choice).
   - `utils/tva.py`, `utils/tva_documente.py`, `utils/mijloc_fix_pdf.py`,
     `setari/views.py` (SUMAR + export) se folosesc de noile servicii.
4. **Teste**
   - Unit (`python manage.py test documente conturi`): se pastreaza valorile
     asteptate (Cortecs 112.2387 / 23.5701 etc.), se inlocuiesc doar
     atribuirile directe ale campurilor derivate
     (`documente/tests.py:127-129,136,146-148,177-180,927-929`).
   - E2E (`make test-e2e`): se rescriu interogarile SQL brute care citesc
     coloanele eliminate — `tests/test_an_complet.py:233,374-412,448-500,
     564-633,679,762,808-847`; se verifica prin interfata/model, nu prin
     coloane de cache. Se actualizeaza valorile choice din
     `tests/helpers.py:22-32` si `tip_tranzactie="42"` -> `"BANCAR"`.
5. **Verificare finala**
   - `python manage.py check`, unit tests, e2e tests.
   - Exportul anual (`/setari/` -> Descarca date) comparat cu cel vechi ca
     header de coloane si valori (in special `Valoare inventar`,
     `Amortizare lunara`, jurnalul de cumparari si `SUMAR.html`).
   - Generare D301/D390 pentru luna cu UE + non-UE (testul existent deja).
6. **Rollback**: `git` + regenerare DB; nu exista date de recuperat.

---

## 6. Decizii care raman de confirmat inainte de implementare

| # | Decizie | Recomandare | Impact daca se alege altfel |
|---|---|---|---|
| D1 | Toate valorile derivate calculate, zero coloane cache | **Da** — O(n) per an e acceptabil la volumul actual; se masoara | Pastrarea `suma_in_ron`/`deducere_in_ron` ca "materialized cache" pastreaza SQL-ul si testele actuale, dar mentine problema divergentei |
| D2 | `CursBnr` tabel vs `lru_cache` existent | **Tabel** pentru determinism in rapoarte | Fara tabel, rapoartele vechi pot cere reteaua si pot obtine cursuri actualizate |
| D3 | `tip_achizitie` derivat din tara vs camp pastrat | **Derivat** (elimina o selectie redundanta din UI) | Daca se pastreaza, raman validarile de consistenta si filtrele actuale, dar si posibilitatea de a gresi |
| D4 | Linii factura: formset vs hidden JSON validat | **Hidden JSON validat** in form, pentru diff mic | Formsetul e mai curat in UI, dar schimba template-ul si fluxul e2e semnificativ |
| D5 | Conturi bancare: formset vs hidden JSON validat | **Formset** | Varianta JSON pastreaza UI-ul, dar lasa logica de parsare in formular |
| D6 | Adaugare `data_incasarii` separat de `data_inserarii` | **Da** | Diff mai mic daca se pastreaza doar `data_inserarii` cu dubla semantica, dar "in asteptare" vs "data operatiunii" raman confundate |
| D7 | Coduri scurte pentru choices | **Da** | Pastrarea valorilor lungi evita modificarile in teste/templates, dar pastreaza bug-ul 2500/5000 si valorile de 170 de caractere in baza |

---

## 7. Riscuri

* **Agregari SQL inlocuite cu Python.** Sunt ~25 de locuri (predominant
  `registre/views.py:250-531` si `cheltuieli/models.py:243-317`). La sute de
  randuri/an costul e neglijabil; la zeci de mii trebuie masurat si eventual
  reintroduse coloane calculate ca `GeneratedField` (SQLite le suporta, Django
  5.2 are suport limitat) — deci D1 trebuie confirmata.
* **Teste e2e cu SQL brut.** O parte din suite verifica direct coloanele de
  cache; rescrierea lor e obligatorie daca se alege D1. Fara ea, testele vor
  esua cu "no such column", nu din cauza functionalitatii.
* **Schimbarea codurilor de choice** afecteaza datele introduse deja in
  `tests/.runtime/test.db` (se sterge odata cu baza) si valorile hardcodate
  din e2e.
* **Parsarea PDF-ului** e best-effort; mutarea ei din `save()` in view poate
  schimba comportamentul la editarea unui document (parsingul se va face doar
  la upload, ceea ce e mai corect, dar e o schimbare de comportament).
* **Generarea documentelor** mutata din `save()` in view inseamna ca
  update-urile din admin/MCP nu vor mai regenera PDF/XML automat; se poate
  adauga un semnal `post_save` daca se doreste pastrarea comportamentului.

---

## Anexa — inventarul campurilor `CheltuialaModel` (36 concrete)

| Camp | Dispozitie propusa |
|---|---|
| `id`, `user`, `nume_cheltuiala`, `suma`, `valuta`, `tip_tranzactie`, `data_inserarii`, `fisier`, `actualizat_la` | pastreaza in baza |
| `deductibila`, `cod_de_clasificare`, `ani_amortizare`, `data_punerii_in_functiune` | pastreaza in baza (input utilizator) |
| `data_iesirii_din_uz`, `modalitate_iesire_din_uz`, `document_justificativ_iesire_din_uz` | pastreaza in baza |
| `furnizor_denumire`, `furnizor_cod_fiscal`, `furnizor_tara`, `numar_factura`, `data_facturii` | pastreaza in baza |
| `suma_in_ron`, `deducere_in_ron` | proprietati (`calcul.py`) |
| `curs_bnr_aplicat`, `baza_in_lei`, `tva_autolichidata` | proprietati (`utils/curs_bnr.py`) |
| `obiect_de_inventar`, `mijloc_fix`, `tip_achizitie`, `scos_din_uz` | proprietati |
| `grupa`, `durata_normala_de_functionare`, `data_inceperii_amortizarii`, `data_amortizarii_complete`, `amortizare_lunara`, `cota_de_amortizare` | proprietati (doar fisa PDF + rapoarte le citesc) |
| `anul/luna_darii_in_folosinta`, `anul/luna_amortizarii_complete` | proprietati (4 coloane -> 4 linii in fisa PDF) |

---

## Anexa — fisiere afectate (orientativ)

| Fisier | Natura schimbarii |
|---|---|
| `utils/models.py`, `utils/valuta.py`, `utils/curs_bnr.py` (nou) | baza comuna, curs BNR stocat |
| `cheltuieli/models.py`, `cheltuieli/catalog.py` (nou), `cheltuieli/calcul.py` (nou), `cheltuieli/forms.py`, `cheltuieli/views.py` | campuri derivate -> proprietati, filtre ORM |
| `facturi/models.py`, `facturi/forms.py`, `facturi/generare.py` (nou), `facturi/views.py` | linii copil, DateField, tip tranzactie, generare documente |
| `incasari/models.py`, `incasari/forms.py`, `incasari/views.py` | data incasarii, suma_in_ron proprietate |
| `setari/models.py`, `setari/forms.py`, `setari/views.py` | conturi copil, CAEN lista, singleton, export |
| `documente/models.py`, `documente/services.py` (nou), `documente/forms.py`, `documente/views.py` | data/suma structurate, parsare in serviciu |
| `registre/views.py`, `utils/tva.py`, `utils/tva_documente.py`, `utils/mijloc_fix_pdf.py`, `mcp_server/tools.py` | consumatori de valori derivate |
| `templates/{cheltuieli,facturi,incasari,inventar,setari,registre,sumar}.html`, `templates/efactura.xml` | nume campuri / choices |
| `tests/helpers.py`, `tests/test_an_complet.py`, `documente/tests.py`, `conturi/tests.py` | asteptari si SQL brut |
| `*/migrations/0001_initial.py` | regenerate de la zero |

---

## 8. Starea implementarii (actualizat dupa implementare)

Schema de mai sus a fost implementata. Verificari: `manage.py check` OK,
`manage.py test documente conturi` -> **82 teste OK**,
`pytest tests/` -> **32 teste e2e OK**. Migrarile vechi au fost sterse si
regenerate (`0001_initial.py` pentru fiecare app, inclusiv noul app `utils`).

Module/noi fisiere:
- `utils/cursuri.py` — modelul `CursBnr` (app `utils`, adaugat in
  `INSTALLED_APPS`, `Makefile` si `tests/conftest.py`) + functiile de curs.
- `cheltuieli/catalog.py` (~3000 linii) si `cheltuieli/calcul.py` — catalogul
  si toate calculele; `calculeaza_deduceri_anului(an)` face o singura trecere
  si e cache-uit pe o semnalatura care include si incasarile (plafonul de
  protocol depinde de venit).
- `facturi/generare.py` — PDF/XML generate la creare, nu in `save()`.
- `documente/services.py` — parsare ANAF la upload.

Abateri fata de propunerea initiala (decizii D4/D5/D7):
- **Conturile bancare** folosesc in continuare un textarea hidden cu JSON in
  formular, dar JSON-ul e validat si transformat in randuri `ContBancar` in
  `SetariForm.save()`. UI-ul (Alpine) si testele raman neschimbate.
- **Liniile facturii** folosesc acelasi mecanism (hidden JSON validat ->
  `LinieFactura`), cu tranzactie atomica; `FacturaModel.produse_sau_servicii`
  ramane disponibil ca proprietate pentru XML/PDF.
- **`TipAchizitie`** a pastrat valorile text (`Romania`, `Servicii UE`,
  `Servicii non-UE`) pentru ca JS-ul din formular le compara direct.
  Celelalte enumuri au primit coduri scurte (`INTEGRAL`, `MIJLOC_FIX`,
  `ACTIVITATE`, `UTIL`, `BANCAR` etc.).
- **`data_inserarii`** a pastrat numele (dif mic); starea de "incasat" e data
  de noul camp `data_incasarii`.
- **`caen_secondar_1..5`** au devenit campuri doar de formular, serialize in
  `caen_secondare` (lista JSON de coduri, nu pseudo-tabela).
- `parse_tip_document` e camp de formular, nu coloana.

Observatii ramase (pentru o etapa ulterioara, nu blocheaza aplicatia):
- `admin.py` inregistreaza modelele simplu; nu exista inline pentru
  `LinieFactura` / `ContBancar`.
- Generarea PDF/XML nu se mai face la editare din admin/MCP (doar la crearea
  prin formular); se poate adauga un semnal daca e nevoie.
- Cache-ul deducerilor e in proces (`cheltuieli.calcul._CACHE`); intr-un
  deployment multi-proces ar trebui mutat in Django cache / Redis.

