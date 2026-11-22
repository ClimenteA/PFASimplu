# Teste end-to-end (Playwright + Faker)

Scenariu complet pe **anul curent**, rulat intr-un browser real (Chromium)
impotriva aplicatiei Django:

1. **Setari** — completare date PFA generate cu Faker (nume, CIF, IBAN-uri
   RON/EUR cu cifra de control valida, cod TVA intracomunitar art. 317,
   IBAN trezorerie pentru plata TVA).
2. **Facturi** — in fiecare luna: o e-factura B2B in Romania (RON) si o
   factura externa (EUR).
3. **Incasari** — max. 5/luna: doua preluate din facturi (butonul „Incasata”,
   cu PDF-ul atasat automat) si 1–3 completate separat in formularul din
   pagina Incasari.
4. **Cheltuieli** — max. 10/luna: consumabile/servicii integral deductibile
   (RON si EUR), obiecte de inventar, auto/utilitati 50%, **servicii UE si
   non-UE cu taxare inversa** (TVA autolichidata 21%, curs BNR automat,
   D301/D390) si **2–3 mijloace fixe pe an** (coduri de clasificare,
   amortizare liniara).
5. **Verificari** — venit total anual **sub 395.000 RON**, TVA autolichidata
   si deducerile calculate corect, amortizari, fisiere generate.

Aplicatia nu accepta date din viitor (`validate_not_future_date`), deci
testele acopera lunile ianuarie → luna curenta. Rulate in ianuarie, acopera
o luna; rulate in decembrie, acopera tot anul.

## Rulare

```bash
# o singura data: browserul pentru Playwright
uv run playwright install chromium

# toate testele (headless)
uv run pytest tests/ -v

# cu browser vizibil / incetinit
uv run pytest tests/ -v --headed
uv run pytest tests/ -v --headed --slowmo 300

# doar o luna / doar o etapa
uv run pytest tests/ -v -k "luna3"
uv run pytest tests/ -v -k "setari or mijloace"
```

## Izolare

- Serverul Django de test porneste automat pe un port liber, cu baza de date
  separata `tests/.runtime/test.db` (prin variabila de mediu
  `PFASIMPLU_DB_PATH`) — **datele reale din `dbsqlite/stocare.db` nu sunt
  atinse**.
- Migrarile sunt generate automat la fiecare rulare (proiectul nu le
  versioneaza, vezi `make purge-migration-dirs`).
- Documentele justificative generate (PDF-uri minimale) sunt in
  `tests/.runtime/files/`.
- Baza de date de test ramane dupa rulare, pentru inspectie manuala.

## Structura

| Fisier | Rol |
|---|---|
| `conftest.py` | fixture-uri: server Django izolat, acces DB, Faker `ro_RO`, limite an/luna |
| `helpers.py` | completare formulare (Alpine.js): setari, facturi, incasari, cheltuieli |
| `test_an_complet.py` | scenariul pe un an, parametrizat pe luni + verificari finale |
