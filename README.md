# PFASimplu

![GitHub all releases](https://img.shields.io/github/downloads/ClimenteA/PFASimplu/total?label=descarcari&style=for-the-badge)

Aplicatie pentru simplificarea gestiunii contabilitatii facuta in partida simpla (versiunea 3).

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Pentru cine este de folos aceasta aplicatie?](#pentru-cine-este-de-folos-aceasta-aplicatie)
- [Poate aplicatia sa faca X,Y,Z?](#poate-aplicatia-sa-faca-xyz)
- [Instalare (aplicatia desktop din Releases)](#instalare-aplicatia-desktop-din-releases)
- [Instalare pt. developeri](#instalare-pt-developeri)
  - [Distributia standalone (build)](#distributia-standalone-build)
- [Instalare pe VPS (Docker + Caddy)](#instalare-pe-vps-docker--caddy)
- [Ghid de utilizare: de la instalare la rutina zilnica](#ghid-de-utilizare-de-la-instalare-la-rutina-zilnica)
- [Setari](#setari)
- [Facturi](#facturi)
- [Incasari](#incasari)
- [Cheltuieli](#cheltuieli)
  - [Servicii cumparate din UE / non-UE (taxare inversa)](#servicii-cumparate-din-ue--non-ue-taxare-inversa)
- [Documente](#documente)
- [TVA intracomunitar: D301, D390 si Jurnal de cumparari](#tva-intracomunitar-d301-d390-si-jurnal-de-cumparari)
  - [D390 VIES pentru clienti UE (vanzari)](#d390-vies-pentru-clienti-ue-vanzari)
- [Inventar](#inventar)
- [Registre](#registre)
- [Actualizare aplicatie](#actualizare-aplicatie)
- [Debug si testare (dezvoltatori)](#debug-si-testare-dezvoltatori)
  - [Rulare in Docker pentru dezvoltare](#rulare-in-docker-pentru-dezvoltare)
  - [Rulare cu uv run (dezvoltare)](#rulare-cu-uv-run-dezvoltare)
  - [Structura codului](#structura-codului)
  - [Teste end-to-end](#teste-end-to-end)
  - [Depanare](#depanare)
- [Observatii](#observatii)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Pentru cine este de folos aceasta aplicatie?

- Pentru cei care detin PFA, PFI, II, etc si pot tine contabilitatea in partida simpla;
- Impozitare in sistem real (fara norma de venit);
- Nu au depasit pragul TVA (venituri sub 395k RON pe an);
- Sunt prestatori de servicii;
- Incaseaza numerar doar B2B maximum 5k/zi ron de la un client SRL/PFA (nu au casa de marcat);

Aplicatia te ajuta sa:
- creezi facturi: e-factura (fara TVA), facturi PDF in mai multe limbi si valute;
- tii la curent toate registrele obligatorii pentru PFA (Registru Jurnal, Registru Fiscal, Registru Inventar);
- calculeaza automat cheltuielile deductibile partial si mijloacele fixe;
- arhivezi declaratiile depuse la ANAF;
- calculeaza automat taxele si impozitele datorate in functie de incasari/cheltuieli;
- calculeaza automat TVA-ul datorat pentru servicii cumparate din UE/non-UE (taxare inversa) si genereaza declaratiile D301/D390 + Jurnalul de cumparari, daca ai cod special de TVA intracomunitar (art. 317);
- genereaza D390 VIES (tip P) si Jurnalul de vanzari pentru facturile emise catre clienti UE marcati „Client UE VIES";


## Poate aplicatia sa faca X,Y,Z?

Aplicatia am facut-o potrivita pentru nevoile mele. Daca pe parcurs voi avea nevoie de X,Y,Z atunci poate voi actualiza aplicatia sa contina si X,Y,Z.

As fi vrut sa adaug mai multe functionalitati, dar nu am cunostinte solide de contabilitate. 
Daca deschizi un `New issue` din tabul `Issues` din aceasta pagina si spui pas cu pas care sunt cerintele voi lua in considerare sa adaug in aplicatie o noua functionalitate (in functie de timp si cunostinte).


## Instalare (aplicatia desktop din Releases)

Aplicatia este disponibila ca executabil in [GitHub Releases](https://github.com/ClimenteA/PFASimplu/releases).

**Cum procedezi:**

1. Deschide [pagina de Releases](https://github.com/ClimenteA/PFASimplu/releases)
   si descarca arhiva `.zip` pentru sistemul tau de operare.
2. Dezarhiveaza-o intr-un folder.
3. Ruleaza executabilul.
4. La **prima pornire** va dura un pic sa-si instaleze dependintele (`pycrucible` e folosit pentru a genera executabilul).
5. Deschide pagina de **inregistrare** si creeaza-ti contul (totul e local, datele tale nu sunt trimise catre un server), apoi completeaza [Setari](#setari).

Executabilul nu are semnatura digitala si vei primi cateva ferestre cu avertismente - ignora-le.
Nu am cumparat semnatura digitala pentru acesta (e scumpa).


**Datele aplicatiei** nu stau langa executabil si nu sunt atinse la upgrade:

| Sistem | Director de date |
|---|---|
| Windows | `%LOCALAPPDATA%\PFASimplu` |
| macOS | `~/Library/Application Support/PFASimplu` |
| Linux | `${XDG_DATA_HOME:-~/.local/share}/pfasimplu` |

In el se afla `db/stocare.db`, `files/` (documente), `logs/`, `staticfiles/` si
`secret_key` (generata aleator la prima pornire). Pentru **backup** copiaza
intregul director (sau foloseste exportul din `Setari`). Pentru **upgrade**
descarca executabilul nou din Releases si inlocuieste-l pe cel vechi (pe care il
poti sterge); datele raman in directorul de mai sus, deci nu sunt afectate. La
pornire se aplica automat migrarile noi; vezi
[Actualizare aplicatie](#actualizare-aplicatie).

Variantele Docker si VPS sunt pentru dezvoltare si self-hosting: vezi
[Instalare pt. developeri](#instalare-pt-developeri) si
[Instalare pe VPS](#instalare-pe-vps-docker--caddy).


## Instalare pt. developeri

Aplicatia e facuta in Python (>= 3.12), Django cu SQLiteDB. Pentru utilizare
zilnica, [aplicatia desktop din Releases](#instalare-aplicatia-desktop-din-releases)
e metoda principala; Docker si `uv run` sunt pentru dezvoltare si self-hosting
(vezi si [Rulare cu uv run](#rulare-cu-uv-run-dezvoltare)).

- clone repo si `make start-local` pentru aplicatia in Docker la `http://localhost:8990`;
- [instaleaza uv](https://docs.astral.sh/uv/getting-started/installation/) si `uv sync`, apoi `make dev` pentru serverul de dezvoltare cu auto-reload;
- `make test-e2e` - ruleaza testele end-to-end (vezi [Debug si testare](#debug-si-testare-dezvoltatori));
- `make migrate-all` / `make purge-db` / `make purge-migration-dirs` - utilitare pentru migrari;
- `make logs-local` / `make stop-local` - loguri, respectiv oprirea aplicatiei locale.

Pe Windows, echivalentul comenzilor make e `.\makefile.bat X` (ex: `start-local`, `stop-local`, `logs-local`, `migrate-all`). Pentru teste: activeaza venvul cu `& D:/PFASimplu/.venv/Scripts/Activate.ps1` (daca PowerShell blocheaza, `Set-ExecutionPolicy Unrestricted -Scope Process`).

Datele stau pe gazda in `appdata/db/` si `appdata/files/` (mount-uri in `docker-compose-local.yaml`) si nu se urca in git. Configurarea locala e in `.env` (ignorat de git, cu valori mock in `.env.example`); .env.prod e doar pentru VPS.

### Distributia standalone (build)

Executabilul descarcat din Releases e construit astfel: `uv build --wheel` →
wheel-ul e integrat in [PyCrucible](https://github.com/razorblade23/PyCrucible) →
un singur binar per sistem de operare.

Construire locala (necesita `uv`; PyCrucible se instaleaza prin `uvx` doar la
build, nu e dependenta a aplicatiei):

```bash
make dist
# rezultat: dist/pfasimplu-<versiune>-<os>-<arhitectura>[.exe]
# + dist/pfasimplu-<versiune>-<os>-<arhitectura>.zip (folosit in release)
```

Pe Windows fara `make`: `uv run --no-project python scripts/build_dist.py`.
Test rapid al binarului: `uv run --no-project python scripts/smoke_dist.py`.

GitHub Actions publica automat un release cu arhivele `.zip` pentru fiecare
platforma la un tag `v*`, la un merge in `main` sau la rulare manuala
(`workflow_dispatch`). Jobul `macos-latest` produce arm64 (Apple Silicon),
iar pentru Mac Intel este nevoie de un job `macos-13`. Binarul e nesemnat;
code signing si notarization macOS sunt pasi urmatori.


## Instalare pe VPS (Docker + Caddy)

Aceasta sectiune e pentru **dezvoltatori si self-hosting**.

Aplicatia ruleaza cu **login/inregistrare pe email + parola** (obligatoriu si in
varianta locala) si **date izolate per utilizator**: fiecare cont isi vede doar
propriile incasari, cheltuieli, facturi, documente si setari, iar fisierele
urcate stau in `appdata/files/user_<id>/` si pot fi descarcate doar de proprietar.

Sunt doua fisiere Docker Compose:

| Fisier | Continut | Acces |
|---|---|---|
| `docker-compose.yaml` | aplicatia + Caddy (TLS automat) - pentru VPS | `https://<domeniu>` |
| `docker-compose-local.yaml` | aplicatia, **fara Caddy** - pentru uz local | `http://localhost:8990` |

Pe VPS (cu Docker si Docker Compose instalate):

```bash
git clone https://github.com/ClimenteA/PFASimplu && cd PFASimplu

# configurarea aplicatiei
cp .env.prod.example .env.prod
# editeaza .env.prod: PFASIMPLU_SECRET_KEY (aleator, lung),
# PFASIMPLU_ALLOWED_HOSTS si PFASIMPLU_CSRF_TRUSTED_ORIGINS cu domeniul tau

# aplicatia + proxy-ul TLS (Caddy); pune domeniul tau in Caddyfile
docker compose -f docker-compose.yaml up -d --build   # sau: make start
```

- Baza de date SQLite si fisierele urcate raman pe gazda, in `appdata/db/`
  si `appdata/files/` (folderul `appdata/` e montat la `/data` in ambele
  compose-uri) - e singurul folder de care ai nevoie pentru backup.
  Nu e inclus in imagine sau in git.
- La pornire containerul aplica migrarile si colectorul de fisiere statice automat.
- Optional: seteaza `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` in
  `.env.prod` pentru a crea un cont de admin (`/admin/`) la prima pornire.
- Optional: `PFASIMPLU_ALLOW_REGISTRATION=0` in `.env.prod` blocheaza crearea de
  conturi noi (pagina de inregistrare devine 404); utilizatorii existenti se pot
  autentifica in continuare. Util implicit: `1` (inregistrare deschisa).
- Pentru test local fara domeniu/TLS: in Caddyfile inlocuieste domeniul cu `:80`
  si in `.env.prod` pune `PFASIMPLU_ALLOWED_HOSTS=localhost` si
  `PFASIMPLU_CSRF_TRUSTED_ORIGINS=http://localhost`.

Varianta locala (fara Caddy/TLS), mereu pornita:

```bash
cp .env.example .env        # daca nu exista deja; continut mock, nu secrete
docker compose -f docker-compose-local.yaml up -d # sau: make start-local
```

Aplicatia e accesibila la `http://localhost:8990`. Portul se schimba prin
`PFASIMPLU_PORT` in `.env` (ex. `PFASIMPLU_PORT=9000`). Cu `restart: unless-stopped` si serviciul
Docker pornit la boot, aplicatia revine singura dupa restartul calculatorului
(mai putin daca a fost oprita manual inainte).


## Ghid de utilizare: de la instalare la rutina zilnica

Ordinea conteaza: aplicatia foloseste datele din `Setari` in toate celelalte pagini (antetul facturilor, IBAN-ul in moneda facturii, calculele de taxe, IBAN-ul trezoreriei pentru TVA).

Toate tabelele (Facturi, Incasari, Cheltuieli, Documente, Inventar) au un formular de cautare `Cauta` / `Coloana` si paginare cate **20 de inregistrari pe pagina** - cautarea se face pe coloana aleasa sau pe toate coloanele, iar filtrele active se pastreaza la paginare. Butoanele CSV/XLSX descarca **toate** inregistrarile contului, nu doar pagina curenta. Coloana `Data Modificare` arata data ultimei modificari a inregistrarii.

**1. Prima deschidere - completeaza Setari**

Deschide aplicatia, autentifica-te (sau inregistreaza-te la prima folosire) si mergi intai in pagina `Setari`: numele PFA-ului, CIF, Nr.Reg.Com., telefon, email, adresa, localitatea (aleasa din sugestii), codul CAEN principal (si, optional, CAEN-uri secundare sub `Adauga CAEN-uri Secundare`) si conturile IBAN (unul per moneda: RON, EUR etc., cu butoane `+ Adauga cont IBAN` / 🗑 pentru stergere). Bifeaza separat `Scutit CAS`, `Scutit CASS` si `Scutit Impozit` doar daca ai statut special (pensionar, persoana cu handicap, profesie liberala cu casa de asigurari proprie etc.). Daca ai cod special de TVA intracomunitar (art. 317), deschide sectiunea `TVA intracomunitar (D301/D390)` si completeaza codul - IBAN-ul trezoreriei se completeaza automat la alegerea localitatii. Salveaza. Fara acest pas, facturile nu au datele emitentului corecte.

**2. Emite prima factura (pagina Facturi)**

Completeaza clientul, seria si numarul (propuse automat: prima factura primeste seria `INV` si numarul `1`, apoi se continua seria existenta cu numarul urmator - poti schimba seria si numarul), articolele (denumire, UM, cantitate, pret), tipul facturii (e-factura pentru B2B in Romania, sau PDF in alta limba/valuta pentru extern), tipul tranzactiei (💳 `BANCAR` sau 💵 `NUMERAR`) si, daca facturezi catre o firma din alt stat UE, comutatorul `Client UE VIES` - campul `CIF/CUI/VAT` trebuie atunci sa contina codul TVA cu prefixul tarii (ex. `ATU77164426`), nu un CIF roman; aplicatia adauga automat in factura mentiunea de taxare inversa in limba formularului ales. La salvare aplicatia genereaza automat PDF-ul facturii (si XML-ul UBL pentru e-factura) si le salveaza cu un prefix-id de 8 caractere. Le descarci din coloanele XML/PDF ale tabelului.

**3. Inregistreaza incasarea (pagina Incasari)**

Cand intra banii: din pagina `Facturi`, click pe 💳 in dreptul facturii - formularul de incasare se completeaza automat (nume incasare, suma, valuta, client, tip tranzactie), iar PDF-ul facturii devine document justificativ atasat incasarii. O factura care are deja incasare nu mai poate avea una a doua (iconita e dezactivata, cu avertisment). Pentru incasari fara factura emisa in aplicatie, completezi formularul din `Incasari` (`Sursa venit`, `Nume incasare`, `Suma`, `Valuta`, `Tip tranzactie`, `Data incasarii`) si urci documentul justificativ (extras de cont, chitanta; mai multe documente → un zip). Conversia in RON se face automat la cursul BNR din ultima zi bancara inaintea datei incasarii. Coloana `VIES` arata daca incasarea provine dintr-o factura cu `Client UE VIES` - pentru acestea se depune lunar D390 (vezi [D390 VIES pentru clienti UE](#d390-vies-pentru-clienti-ue-vanzari)).

**4. Inregistreaza cheltuielile (pagina Cheltuieli)**

De fiecare data cand cumperi ceva pentru activitatea PFA-ului: urci factura/bonul, alegi deductibilitatea (integral, obiect de inventar, mijloc fix peste 5000 RON cu amortizare, sau una din limitele speciale: 50% pentru autovehicule/chirii/utilitati folosite si personal, 2% mese protocol, burse private max. 5%, sport/fitness max. 100 EUR/an, pensie pilon III / ocupationala / PEPP / ETF / asigurari medicale private max. 400 EUR/an, salarii, ajutoare pentru angajati etc.), completezi `Tip tranzactie` (bancar/numerar) si, pentru servicii din UE/non-UE, alegi `Origine furnizor` - TVA-ul prin taxare inversa se calculeaza singur. Pentru mijloace fixe alegi direct varianta din campul `Deductibila`: sediu social folosit si in scop personal (amortizare 50%), autoturism M1 (limita 1500 lei/luna) sau autoturism M1 cu exceptie (amortizare integrala). Obiectele de inventar si mijloacele fixe apar automat in pagina [Inventar](#inventar) cu numar de inventar; pentru mijloacele fixe se genereaza fisa de mijloc fix (PDF), iar amortizarea lunara apare in Registrul fiscal.

**5. Arhiveaza relatia cu ANAF (pagina Documente)**

Dupa ce depui Declaratia Unica (D212) sau platesti taxele, urci aici recipisa/dovada platii - datele relevante (an, sume, index) se extrag automat din PDF. La fel pentru recipisele D301/D390.

**6. Verifica situatia (pagina Registre)**

Oricand, dar musai inainte de a completa Declaratia Unica: cardurile cu totaluri (neincasate, incasari brut/net, cheltuieli) si taxele estimate (CAS, CASS, impozit), graficul pe luni si registrele obligatorii, in 5 taburi: `Registru jurnal`, `Registru fiscal`, `Registru inventar`, `Jurnal Cumparaturi` si `Jurnal Vanzari`. Sumele se pot vedea in RON sau EUR, pe orice an. Sub titlu gasesti si totalul platilor catre stat pe toti anii, totalul incasarilor nete si restul de plata.

**7. Lunar, daca ai cod TVA intracomunitar:** in pagina `Cheltuieli` filtreaza `Cheltuieli externe (TVA)` pe luna si anul trecute si descarca zip-ul cu D301/D390 completate, iar in pagina `Incasari` filtreaza `Incasari din UE (TVA)` si descarca D390 pentru facturile emise catre clienti UE. Depune declaratiile pana pe 25, incarca recipisele in Documente si plateste TVA-ul datorat la trezorerie (detalii in [TVA intracomunitar](#tva-intracomunitar-d301-d390-si-jurnal-de-cumparari)).

**8. La final de an:** din `Setari` → `Exporta datele din aplicatie` alegi anul si primesti un zip cu toate documentele justificative, registrele in Excel, fisele mijloacelor fixe si `SUMAR.html` - arhiva completa pentru acel an, de pastrat pentru controlul ANAF.

**Ce face aplicatia in spate cu fisierele:**
- fiecare fisier urcat sau generat (facturi PDF/XML, justificative, fise mijloc fix) e salvat in `appdata/files/` cu un prefix-id unic de 8 caractere (ex. `0x4rf2KW_factura_PFT-1.pdf`), ca sa nu existe coliziuni de nume; la re-incarcarea unui fisier deja prefixat, prefixul vechi e inlocuit;
- fisierele stau in `appdata/files/user_<id>/` (directoarele sunt montate de pe gazda in container) si pot fi descarcate doar de proprietar;
- exporturile CSV/XLSX ale registrelor si zip-urile generate (D301/D390, exportul pe an) se construiesc temporar in `appdata/files/extracts/` si se livreaza la download;
- la stergerea unei inregistrari din aplicatie, fisierul atasat ei este sters automat de pe disc (django-cleanup); `Sterge toate datele` din Setari sterge si baza de date si fisierele;


## Setari 

In pagina `Setari` trebuie sa adaugi datele pfa-ului tau: nume, CIF, Nr.Reg.Com., telefon, email, adresa, localitatea (din sugestii), codul CAEN principal si, optional, pana la 5 CAEN-uri secundare (butonul `+ Adauga CAEN-uri Secundare`).
Sunt trei casute separate pentru scutiri: `Scutit CAS`, `Scutit CASS`, `Scutit Impozit` - bifeaza-le doar daca ai statut special (pensionar, persoana cu handicap, profesie liberala cu casa de asigurari proprie etc.); aplicatia foloseste bifa respective la calculul taxelor din pagina Registre.
Poti sterge toate datele.
Aceasta pagina trebuie completata la prima deschidere a aplicatiei.
Cam rar vei schimba datele din aceasta pagina.
Poti adauga mai multe conturi IBAN (RON, EUR, USD etc.), cate unul pentru fiecare moneda, direct in formular (butonul `+ Adauga cont IBAN`, respectiv iconita 🗑 pentru fiecare rand). La emiterea unei facturi se foloseste automat contul IBAN in moneda facturii, iar daca nu exista un cont in acea moneda, se foloseste contul de RON.
Sectiunea `TVA intracomunitar (D301/D390)` e colapsata initial si se deschide cu butonul cu acelasi nume (vezi mai jos).

Cu butonul `Exporta datele din aplicatie` descarci un zip cu datele pentru **anul selectat**. Zip-ul contine:
- `documente/`, `cheltuieli/`, `incasari/` - documentele justificative urcate in aplicatie pentru anul selectat;
- registrele anului in format `.xlsx`: Registrul Jurnal, Registrul Inventar, Registrul Fiscal, Jurnalul de cumparari si Jurnalul de vanzari;
- `fise_mijloace_fixe/` - fisele mijloacelor fixe (PDF);
- `SUMAR.html` - metricile anului, in acelasi stil ca aplicatia (se deschide in orice browser): total incasari/cheltuieli, venit net, taxe si impozite de platit (CAS, CASS, impozit), ultima serie si numar de factura emisa (in anul exportat si in aplicatie), medii lunare, cea mai mare incasare/cheltuiala, incasari pe surse, cheltuieli pe deductibilitate si tabelele de amortizare per mijloc fix pana la amortizarea completa.


Daca ai **cod special de TVA intracomunitar (art. 317 Cod fiscal)** si cumperi servicii din UE/non-UE (ex. Google, Cloudflare, OpenAI), deschide sectiunea `TVA intracomunitar (D301/D390)` si completeaza:
- **Cod TVA intracomunitar** - codul special din certificatul de inregistrare in scopuri de TVA, fara prefixul RO. Este diferit de CIF-ul normal al PFA-ului: pentru facturi din UE se foloseste codul special, pentru non-UE codul normal (aplicatia alege automat codul corect);
- **IBAN trezorerie pentru plata TVA** - se completeaza **automat cand selectezi localitatea** (campul `Alege localitatea`): aplicatia are tabelul IBAN-urilor extras din [sursele oficiale ANAF](https://www.anaf.ro/anaf/internet/ANAF/asistenta_contribuabili/plata_oblig_fiscale/coduri_iban) (202 trezorerii operative, inclusiv sectoarele Bucurestiului) si stie contul `20A100101 - TVA incasata pentru operatiuni interne` pentru localitatea ta. Linkul PDF-ului ANAF ramane afisat ca sa poti verifica. Daca tabelul `src/static/iban_trezorerie.json` lipseste, aplicatia il descarca automat de pe ANAF la prima salvare a Setarilor (necesita conexiune la internet; dureaza cateva minute). Daca localitatea nu are trezorerie operativa proprie (sate/comune), cauta IBAN-ul in lista ANAF pentru judetul tau si completeaza-l manual. TVA-ul din D301 NU se plateste in contul unic.

![setari - datele PFA](readmepics/setari.png)



## Facturi

In pagina `Facturi` poti crea facturi pentru clienti din afara tarii, precum si e-factura pentru B2B in Romania. 
Factura generata aici este valabila pentru **PFA-urile neplatitore de TVA**.
Odata ce datele sunt completate in formular ele vor putea fi folosite si pentru facturi viitoare.
Pentru e-factura valoarea din campul 'Alege localitatea' trebuie sa fie una din valorile sugerate pe masura ce tastezi.
Fisierul generat XML este conform [XML-UBL versiunea 1.0.3](https://www.anaf.ro/CompletareFacturaSimplificat/faces/factura/informatiigenerale.xhtml).
Validarea fisierului XML a fost facuta pentru standard [FACT1](https://www.anaf.ro/uploadxmi/).
Poti prelua date CUI firma [de aici.](https://mfinante.gov.ro/apps/agenticod.html?pagina=domenii).

Campurile: Serie, Numar factura vor fi completate automat in functie de facturile din trecut. 
Seria + numarul facturii sunt verificate sa fie unice in baza de date.
Pe masura ce completezi campul Nume Client vor aparea sugestii de clienti existenti - 
cu un click poti selecta clientul si formularul va fi completat automat (nume, CIF, adresa, localitate, tip factura, tip tranzactie, valuta, date de contact si starea `Client UE VIES`).
In campul Tip factura poti alege sa generezi factura in alta limba (non e-factura). 
Poti schimba si valuta in care emiti factura (pentru e-factura si factura in romana valuta e blocata pe RON).

Campul `Tip tranzactie` (💳 BANCAR / 💵 NUMERAR) se preia in incasarea generata din factura si apare in Registrul jurnal pe coloanele de incasari bancare, respectiv numerar.

Comutatorul `Client UE VIES` se bifeaza doar pentru clienti persoane impozabile din alte state UE, care datoreaza ei TVA-ul prin taxare inversa. Campul `CIF/CUI/VAT` trebuie sa contina codul TVA complet cu prefixul tarii (ex. `ATU77164426`); un CIF roman (`RO...`) este respins. Aplicatia completeaza automat campul `Nota` cu mentiunea de taxare inversa in limba facturii alese si foloseste factura pentru D390 VIES (vezi [D390 VIES pentru clienti UE](#d390-vies-pentru-clienti-ue-vanzari)).

Din coloanele XML si PDF poti descarca facturile generate. In dreapta sus a tabelului sunt 2 butoane pentru a descarca toate facturile in format CSV sau XLSX. In coloana Del. poti sterge o factura. Tabelul are si cautare pe coloane si paginare; coloanele arata CIF/CUI/VAT, numele clientului, totalul, valuta, tipul tranzactiei, seria/numarul, emailul, telefonul, scadenta si starea incasarii.

Din coloana **Incasata** (butonul 💳) treci direct la pagina [Incasari](#incasari) cu formularul precompletat din factura respectiva (nume incasare, suma, valuta, client, tip tranzactie), iar PDF-ul facturii este atasat automat ca document justificativ al incasarii. Daca factura are deja o incasare, butonul e dezactivat si trebuie stearsa incasarea existenta pentru a o adauga din nou.

Optional: Daca dai click pe Mai mult vei putea completa si alte date ale clientului precum:
Nr.Registru Comertului, Telefon, Email, Data Emitere factura (completata automat pentru ziua curenta), Data scadenta (calculata automat la 30 in viitor fata de ziua curenta) si Nota (unde poti adauga niste mentiuni in factura).


![facturi](readmepics/facturi.png)



## Incasari

Aici poti aduga documentele justificative (facturi, chitante) prin care ai incasat bani oferind produse sau servicii cu PFA-ul tau. Daca ai incasari din alte surse decat din emitere facturi/bonuri selecteaza o alta sursa a venitului. Completeaza campul `Nume incasare` (de obicei numele clientului + seria si numarul facturii). In cazul incasarilor in alta moneda decat RON conversia va fi facuta automat la cursul zilei bancare anterioare datei din campul `Data incasarii`. Completeaza 'Data incasare' doar daca ai incasat banii, lasa campul gol daca nu ai incasat inca (vei putea modifica mai tarziu) - in tabel aceste randuri apar cu `Neincasata`. Campul `Tip tranzactie` (💳 BANCAR / 💵 NUMERAR) e preluat automat de la factura cand incasarea vine din pagina Facturi si determina coloana din Registrul jurnal in care se inscrie suma.

Tabelul arata numele incasarii, coloana `VIES` (Da/Nu, dupa cum factura e marcata `Client UE VIES`), suma primita, valuta, suma in RON, tipul tranzactiei, data incasarii, sursa venitului si data modificarii; are cautare pe coloane si paginare. Cu un click in coloana Mod. poti modifica o incasare, din coloana Doc. o poti descarca, iar in coloana Del. o poti sterge. Daca trebuie sa adaugi mai mult de un document poti crea un zip cu toate documentele necesare.

Filtrul `Incasari din UE (TVA)` de deasupra tabelului arata incasarile din facturile cu `Client UE VIES`, grupate pe luna emiterii si pe an; butonul `Descarca` genereaza D390 VIES completat, jurnalul de vanzari in Excel si facturile emise (vezi [D390 VIES pentru clienti UE](#d390-vies-pentru-clienti-ue-vanzari)).


![incasari](readmepics/incasari.png)



## Cheltuieli

Aici poti aduga documentele justificative (facturi, chitante) pentru cheltuielile pe care le-ai facut in scopul prestarii activitatii tale de PFA. Campul `Tip tranzactie` (💳 BANCAR / 💵 NUMERAR) determina coloana din Registrul jurnal in care se inscrie plata.

Campul `Deductibila` alege regula fiscala a cheltuielii. Optiunile sunt in ordinea din aplicatie, iar limitele se calculeaza automat: daca suma depaseste plafonul, vezi mesajul cu suma ramasa disponibila.

| Optiune in `Deductibila` | Cand o alegi si ce regula se aplica | Exemplu |
|---|---|---|
| `Deductibila integral` | Cheltuiala curenta efectuata in scopul activitatii si justificata prin document: se deduce toata suma in anul platii (art. 68 alin. 4 lit. a). | Toner 120 RON; abonament de contabilitate 200 RON/luna. |
| `Obiect de inventar (deductibil integral)` | Bun care nu se consuma imediat, dar e sub pragul de mijloc fix de 5000 RON (art. 28 alin. 2 lit. b). Se deduce integral la achizitie si apare in [Inventar](#inventar). | Scaun de birou 800 RON; imprimanta 1.200 RON. |
| `Mijloc fix peste 5000 RON (ded. integral cu amortizare)` | Regula generala pentru bunurile amortizabile: valoarea se recupereaza lunar prin amortizare, nu prin deducerea integrala a facturii (art. 28 alin. 1-2 si art. 68 alin. 4 lit. d). Se completeaza codul de clasificare, data punerii in functiune si anii de amortizare. | Laptop 6.000 RON, cod `2.2.9.`, 2 ani → 250 RON/luna. |
| `Mijloc fix peste 5000 RON (sediu social amortizare 50%)` | Sediu social intr-o cladire de locuit, folosit si in scop personal: amortizarea se deduce in procent de 50% (art. 28 alin. 12 lit. i^1). Daca e folosit personal de asociati/actionari, amortizarea nu se deduce deloc. | Apartament de 40.000 RON folosit ca sediu si locuit → se deduce 50% din amortizarea lunara. |
| `Mijloc fix peste 5000 RON (Autoturism M1 limita 1.500 lei/luna)` | Autoturism M1 (cel mult 9 scaune, inclusiv soferul) care nu e folosit exclusiv in activitate: amortizarea e deductibila cel mult 1.500 RON/luna (art. 28 alin. 14). | Masina 60.000 RON / 2 ani → 2.500 RON/luna calculat, dar se deduce 1.500 RON/luna. |
| `Mijloc fix peste 5000 RON (Autoturism M1 cu exceptie art. 28 alin. 14, amortizare integrala)` | Autoturism M1 folosit **exclusiv** in una dintre situatiile de la art. 28 alin. 14 lit. a)-d): urgenta, paza/protectie, curierat; agenti de vanzari si achizitii (inclusiv test drive si demonstratii); transport de persoane cu plata (taximetrie); prestari cu plata (inchiriere, leasing operational, scoli de soferi). Fara plafon lunar. | Masina de curierat 60.000 RON / 2 ani → 2.500 RON/luna, integral. |
| `Vehicule nefolosite exclusiv in activitate, 50% (art. 68 alin. 7 lit. k)` | Cheltuieli de functionare, intretinere si reparatii ale unui vehicul folosit si personal: se deduce 50% (art. 68 alin. 5 lit. j si Normele metodologice, pct. 7 alin. 7). **Nu se aplica amortizarii**, care are regula ei la art. 28. Pentru 100% e necesara foaia de parcurs. | Combustibil 1.000 RON → 500 RON dedusi; RCA 800 RON → 400 RON dedusi. |
| `Burse private max. 5% din baza de calcul (art. 68 alin. 5 lit. a)` | Bursa privata platita conform legii, in limita a 5% din baza de calcul de la art. 68 alin. 6 (venitul brut minus celelalte cheltuieli deductibile, fara protocol si burse). | Bursa 2.000 RON; daca baza de calcul e 30.000 RON, se deduce 1.500 RON. |
| `Sport, sali de fitness etc. max. 100 EUR pe an` | Abonament sportiv platit in scop personal la un furnizor cu CAEN 9311, 9312 sau 9313, cel mult 100 EUR/an (art. 68 alin. 5 lit. r). Plafonul se cumuleaza pe an. | Abonament sala 600 RON/an → se deduce 600 RON sau echivalentul a 100 EUR, daca e mai mic. |
| `Pensie pilon III max. 400 EUR pe an` | Contributii la fonduri de pensii facultative, platite in scop personal, max. 400 EUR/an (art. 68 alin. 5 lit. g; pentru 2026 vezi si notele OUG 8/2026). | 2.000 RON/an → se deduce echivalentul a 400 EUR. |
| `Pensie ocupationala max. 400 EUR pe an (din 2026)` | Contributii la scheme de pensii ocupationale, max. 400 EUR/an (art. 68 alin. 5 lit. g^1 si notele OUG 8/2026). | 1.500 RON/an → se verifica plafonul de 400 EUR. |
| `Produs paneuropean de pensii (PEPP) max. 400 EUR pe an (din 1.03.2026)` | Contributii PEPP platite in scop personal, max. 400 EUR/an (art. 68 alin. 5 lit. g^2 si notele OUG 8/2026). | 1.000 RON platiti in aprilie 2026 → se verifica plafonul de 400 EUR. |
| `ETF max. 400 EUR pe an (din 1.03.2026)` | Sume platite pentru actiuni/titluri ETF prin entitatile de la art. 96^1 alin. 1, max. 400 EUR/an, **fara costurile tranzactiei** (art. 68 alin. 5 lit. s si OUG 8/2026). Pastreaza documentul cu elementele cerute de lege. | 3.000 RON in ETF → se deduce min(3.000 RON, 400 EUR), fara comisionul de tranzactie. |
| `Asigurari medicale private max. 400 EUR pe an` | Prime de asigurare voluntara de sanatate si servicii medicale prin abonament, platite in scop personal, max. 400 EUR/an (art. 68 alin. 5 lit. h). | Abonament medical privat 1.800 RON/an → se deduce echivalentul a 400 EUR. |
| `Mese protocol max. 2% baza de calcul` | Cheltuieli de protocol, in limita a 2% din baza de calcul de la art. 68 alin. 6 (art. 68 alin. 5 lit. b). Cadourile de mica valoare (≤ 100 RON, exclusiv TVA) acordate in actiuni de protocol nu sunt livrari de bunuri (Normele metodologice, pct. 7 alin. 12 lit. a). | Cina cu clienti 1.000 RON; limita = 2% din baza de calcul. |
| `Deductibila integral salarii` | Salarii si sume asimilate salariilor platite angajatilor, deductibile integral (art. 68 alin. 4 lit. c). Baza lor determina si plafonul de 5% pentru ajutoare. | Salariu brut 6.000 RON/luna. |
| `Ajutoare diverse pt. angajati max. 5% din total salarii pe an` | Cheltuieli sociale pentru angajati, pana la 5% din valoarea anuala a cheltuielilor cu salariile (art. 68 alin. 5 lit. c). | Cadou angajat 500 RON, cand salariile anuale insumeaza 100.000 RON (limita 5.000 RON). |
| `Contributii obligatorii asociatii, organizatii max. 5% din brut` | Contributii profesionale obligatorii datorate organizatiilor profesionale din care faci parte, max. 5% din venitul brut realizat (art. 68 alin. 5 lit. q). | Cotizatie obligatorie 1.000 RON, la un brut de 50.000 RON (limita 2.500 RON). |
| `Cotizatii voluntare asociatii, organizatii max. 4000 EUR pe an` | Cotizatii voluntare la asociatii profesionale, max. 4.000 EUR/an (art. 68 alin. 5 lit. p). | Cotizatie 1.500 RON/an. |

Toate limitele in euro se transforma in lei la cursul mediu comunicat de BNR pentru anul platii (Normele metodologice, pct. 6). Plafoanele anuale se verifica la fiecare cheltuiala, in ordinea introducerii, separat pentru fiecare categorie.

Eticheta `Vehicule nefolosite exclusiv in activitate, 50% (art. 68 alin. 7 lit. k)` pastreaza numerotarea mai veche: in textul consolidat 2026-10-25 regula cheltuielilor cu autoturismele e la art. 68 alin. (5) lit. j), cu trimitere la alin. (7) lit. k); detaliile (ce cheltuieli intra sub limita si foaia de parcurs) sunt in Normele metodologice, pct. 7 alin. (7).

![cheltuieli - optiuni mijloc fix in campul Deductibila](readmepics/cheltuieli_mijloc_fix.png)

Unele cheltuieli au nevoie de documente justificative in plus pe langa bonul sau factura care justifica cheltuiala. Achizitiile care nu isi pierd valoarea in timp (terenuri, aur, case) nu sunt deductibile. Daca trebuie sa adaugi mai mult de un document poti crea un zip cu toate documentele necesare.

Tabelul arata suma in valuta, suma in RON, suma dedusa in RON, TVA-ul autolichidat (cu badge 🇪🇺 / 🌍), tipul tranzactiei, data cheltuielii, tipul deductibilitatii si data modificarii; are cautare pe coloane si paginare. Regulile de deductibilitate si limitele sunt explicate pe larg in [Ghidul PFA in sistem real](GHID_PFA_SISTEM_REAL.md).

![cheltuieli](readmepics/cheltuieli.png)

Atunci cand ai de adaugat un obiect de inventar cu valoarea peste 5000 RON trebuie sa selectezi una dintre variantele `Mijloc fix peste 5000 RON ...` din campul `Deductibila`. In campul `Nume cheltuiala` apar sugestii cu denumirile folosite anterior; cautarea din tabel filtreaza si pe acest camp (ca si pe celelalte coloane).

Uite un exemplu pentru a amortiza o cheltuiala amortizabila cu un Laptop. 
Cel mai apropiat de un laptop in tabel este valoarea `Calculatoare electronice` care are codul `2.2.9.` 
si o perioada de amortizare intre 2 si 4 ani. 


> Amortizare: 2-4 ani. COD: '2.2.9.' din GRUPA 2. INSTALATII TEHNICE, MIJLOACE DE TRANSPORT, ANIMALE SI PLANTATII - 2.2. APARATE SI INSTALATII DE MASURARE, CONTROL SI REGLARE.. Active fixe: Calculatoare electronice si echipamente periferice. Masini si aparate de casa, control si facturat.

Odata introduse aceste date, aplicatia va calcula automat amortizarea acelui activ fix.

![cheltuieli_amortizare](readmepics/cheltuieli_amortizare_nou.png)

### Servicii cumparate din UE / non-UE (taxare inversa)

Daca ai cod special de TVA intracomunitar (art. 317) si cumperi servicii de la furnizori din afara Romaniei (ex. Google, Cloudflare, OpenAI, Cortecs), la adaugarea cheltuielii alege la **Origine furnizor** `Servicii din UE` sau `Servicii din afara UE`. Apare o sectiune suplimentara cu datele de pe factura furnizorului (care are de obicei mentiunea *reverse charge / 0% VAT*):

- **Denumire furnizor** - pe masura ce tastezi apar sugestii din facturile anterioare; cu un click codul TVA si tara se precompleteaza automat;
- **Tara furnizor** - lista este filtrata dupa originea aleasa: `Servicii din UE` arata doar cele 27 de state membre UE ([sursa oficiala](https://european-union.europa.eu/node/288/rss_ro)), `Servicii din afara UE` doar tarile non-UE (Marea Britanie este non-UE dupa Brexit); UE/non-UE se deduce automat din tara, iar daca ai ales gresit tipul, aplicatia il corecteaza;
- **Cod TVA / cod fiscal furnizor** - pentru UE codul TVA complet cu prefixul tarii (ex. `ATU77164426`), pentru non-UE codul fiscal strain (ex. EIN `27-0805829`), daca exista;
- **Numar factura** si **Data facturii** (exigibilitatea TVA) - daca data facturii lipseste se foloseste data cheltuielii.

**Calculele se fac automat la salvare**, nu trebuie sa completezi nimic manual:
- cursul BNR din data exigibilitatii (data facturii), luat automat din `cursvalutarbnr`;
- baza in lei = valoarea in valuta x curs;
- TVA autolichidata = baza x 21% (cota standard);
- TVA-ul se adauga automat la cheltuiala deductibila (este o cheltuiala a PFA-ului, platita la ANAF prin D301) - vezi coloana `TVA` din tabel, cu badge 🇪🇺 (UE) sau 🌍 (non-UE).

Odata salvata, cheltuiala apare automat in **Jurnalul de cumparari (TVA)** din pagina [Registre](#registre) (tab `Jurnal Cumparaturi`) - este generat din calcul, nu trebuie inserat nimic. Declaratiile D301/D390 se descarca din filtrul „Cheltuieli externe (TVA)" de deasupra tabelului - vezi sectiunea [TVA intracomunitar](#tva-intracomunitar-d301-d390-si-jurnal-de-cumparari).


## Documente

Aici poti introduce documentele create in relatia cu ANAF. Declaratii, dovezi plati taxe si impozite si alte documente pe care le consideri importante. Daca nu ai depasit plafonul TVA de 395000 RON pe an si nu ai angajati (poti avea 3 angajati) singura declaratie pe care trebuie sa o completezi este Declaratia Unica 212. Daca ai depasit plafonul TVA sau ai angajati poate un SRL ar fi mai potrivit. Daca nu gasesti tipul declaratiei alege 'Document util' si completeaza in campul 'Mentiuni' detalii despre documentul incarcat.

In cazul dovezii platii de impozite (pdf-ul primit de la ghiseul.ro) si al declaratiei unice datele relevante sunt automat extrase din PDF-ul incarcat. Campul `Document pentru data` (implicit ziua curenta) se foloseste pentru anul in care se arhiveaza documentul; in tabel apare coloana `Doc. Anul`.

Recipisele D301/D390 primite de la ANAF se incarca tot aici - tipul declaratiei, perioada, CIF-ul si indexul de incarcare se detecteaza automat din PDF. Declaratiile in sine se genereaza din pagina [Cheltuieli](#tva-intracomunitar-d301-d390-si-jurnal-de-cumparari), respectiv [Incasari](#d390-vies-pentru-clienti-ue-vanzari). Tabelul are cautare pe coloane, paginare si coloana `Data Modificare`.

![documente](readmepics/documente.png)



## TVA intracomunitar: D301, D390 si Jurnal de cumparari

Pentru PFA-urile cu **cod special de TVA intracomunitar (art. 317 Cod fiscal)** aplicatia acopera doua fluxuri distincte:

1. **cumpararea** de servicii din UE / afara UE, unde TVA-ul se datoreaza in Romania prin **taxare inversa** (furnizorul factureaza 0% TVA, beneficiarul calculeaza si plateste 21% la ANAF);
2. **vanzarea** de servicii catre clienti persoane impozabile din UE (facturi marcate `Client UE VIES`), unde taxa e datorata de client in statul lui, iar tu depui doar D390 (informativ) - vezi [D390 VIES pentru clienti UE](#d390-vies-pentru-clienti-ue-vanzari).

**Ce se depune:**

| Situația | D301 | D390 VIES | Codul folosit |
|---|---|---|---|
| Furnizor din UE (Austria, Irlanda, Germania etc.) | Da - secțiunea 4 + secțiunea 4.1 | Da - tip S | Codul special de TVA intracomunitar |
| Furnizor din afara UE (SUA, UK, Canada etc.) | Da - doar secțiunea 4 | Nu | Codul normal al PFA-ului (CIF) |
| Client din UE (factura cu `Client UE VIES`) | Nu | Da - tip P (prestari de servicii) | Codul special de TVA intracomunitar |

**Fluxul in aplicatie (pagina Cheltuieli, filtrul „Cheltuieli externe (TVA)"):**

1. **Adaugi cheltuielile** cu origine UE/non-UE (vezi [Cheltuieli](#cheltuieli)) - cursul BNR, baza si TVA-ul se calculeaza automat;
2. **Filtrezi pe luna si an** - din selectorul „Cheltuieli externe (TVA)" de deasupra tabelului alegi luna de raportare (lunile cu facturi UE/non-UE, grupate dupa data facturii, sau `UE + non-UE, tot anul`); selectorul `Anul` apare dupa activarea filtrului si permite alegerea altui an; tabelul arata doar facturile pentru care trebuie completate declaratiile;
3. **Descarci** - un click pe butonul `Descarca` si primesti un zip cu declaratiile completate in **Markdown**, **grupate in cate un folder pentru fiecare cod fiscal**, cu prefix dupa tipul codului:
   - **`TVA-<cod>`** (codul special de TVA intracomunitar, art. 317): **D301** (sectiunile 4 + 4.1) + **D390 VIES** (tip S, cod operator fara prefixul tarii, baza rotunjita la intreg) + jurnalul de cumparari in **Excel** doar cu facturile UE + **facturile furnizorilor** (subfolder `facturi/`);
   - **`CIF-<cod>`** (codul normal al PFA-ului): **D301** (doar sectiunea 4) + jurnalul de cumparari in **Excel** doar cu facturile non-UE + **facturile furnizorilor** (subfolder `facturi/`);
   - fiecare D301 contine antetul, sectiunile cu toate valorile, termenul si **instructiunea de plata** (IBAN trezorerie, cod bugetar `20A100101`, suma, CIF platitor);
   - jurnalul de cumparari pe toata luna este disponibil si separat in [Registre](#registre) > `Jurnal Cumparaturi` (CSV/XLSX), cu referinta `15-16`;
4. **Depui** declaratiile online: ai nevoie de un **cont SPV inregistrat pe codul de TVA intracomunitar** (pe acel cont te loghezi si preiei recipisele). Intră pe [e-guvernare.ro](https://www.e-guvernare.ro/) → click pe **DEPUNERE DECLARATII ANAF** (redirecționează către [decl.anaf.mfinante.gov.ro](https://decl.anaf.mfinante.gov.ro/my.policy)) → **Authentificare cu certificat** (certificat digital calificat de la certDigital, DigiSign etc.) → completezi PDF-ul inteligent cu valorile din fisierele Markdown, îl validezi și semnezi (suma de control si nr. de evidenta a platii se genereaza de aplicatia oficiala ANAF la validare), îl urci, apoi te loghezi în SPV-ul pe codul TVA, descarci recipisa și verifici să fie fără erori de încărcare; termen: **25 inclusiv a lunii urmatoare**;
5. **Incarci recipisa** in pagina [Documente](#documente) - tipul (D301/D390), perioada, CIF-ul si indexul de incarcare se detecteaza automat din PDF;
6. **Platesti** TVA-ul in contul trezoreriei din Setari (instructiunea de plata din fisierul D301 are toate datele).

Daca lipsesc date din Setari (cod TVA intracomunitar, IBAN trezorerie) apar avertizari la descarcare.

![cheltuieli_tva](readmepics/cheltuieli_tva.png)

**Jurnalul de cumparari** este disponibil si in pagina [Registre](#registre) (tab `Jurnal Cumparaturi`), cu descarcare CSV/XLSX pe luna sau pe tot anul. Totalul documentului include TVA autolichidata, chiar daca furnizorul a facturat 0% TVA.

### D390 VIES pentru clienti UE (vanzari)

Pentru facturile emise catre clienti persoane impozabile stabiliti in alte state UE, locul prestarii e in statul clientului, iar **clientul datoreaza TVA-ul prin taxare inversa**. Tu nu colectezi si nu platesti TVA pentru aceste facturi, dar trebuie sa le raportezi lunar in **D390 VIES**, la linia **P - Prestari intracomunitare de servicii**.

Fluxul in aplicatie:

1. **Marchezi ca `Client UE VIES`** in formularul de factura (pagina [Facturi](#facturi)) si completezi `CIF/CUI/VAT` cu codul TVA al clientului, cu prefixul tarii (ex. `ATU77164426`); aplicatia adauga automat mentiunea de taxare inversa in factura;
2. **Inregistrezi incasarea** (pagina [Incasari](#incasari)) - coloana `VIES` devine `Da`;
3. **Filtrezi** in pagina Incasari optiunea `Incasari din UE (TVA)` pe luna (sau `Clienti UE, tot anul`) si pe an;
4. **Descarci** zip-ul cu **D390 completat in Markdown** (cu ghid pas cu pas pentru aplicatia ANAF), **jurnalul de vanzari in Excel** si **facturile emise** catre clientii UE (PDF/XML);
5. **Depui D390** pana pe 25 inclusiv a lunii urmatoare, online, cu certificat digital, in SPV-ul deschis pe codul de TVA intracomunitar, apoi descarci recipisa si o arhivezi in [Documente](#documente).

Declaratia contine codul tau de art. 317 (calitatea „Persoane inregistrate conform art. 317"), codurile clientilor **fara prefixul tarii** si baza in lei rotunjita la intreg. Nu se completeaza D301 si nicio suma de plata.

> **Atentie:** aplicatia genereaza codul **P** (prestari de servicii). Daca vinzi **bunuri** livrate intracomunitar, codul corect e **L** si trebuie corectat in aplicatia ANAF inainte de depunere. Nu se depune D390 pentru clienti scutiti de TVA in statul membru al clientului sau pentru persoane neimpozabile. Vezi [Ghidul PFA in sistem real](GHID_PFA_SISTEM_REAL.md) pentru detalii.

> **Atentie generala:** codul TVA intracomunitar (art. 317) nu confera calitatea de platitor normal de TVA (art. 316). Aceasta functionalitate acopera regimul art. 317 (D301/D390), nu decontul D300. Pentru situatii speciale confirma tratamentul cu contabilul.



## Inventar

Aici gasesti tabelul cu toate obiectele de inventar si mijloacele/activele fixe achizitionate pana acum. Tot aici poti scoate din inventar un obiect de inventar sau mijloc fix. Daca ai vandut obiectul de inventar/mijlocul fix va trebui sa-l introduci si la incasari la Sursa venit: 'Venit din alte surse'. 

Pentru a scoate un obiect de inventar din uz trebuie sa dai click in coloana Mod. pe iconita de modificare. 
Formularul va fi completat cu datele salvate anterior pe care acum le poti modifica si salva: bifezi „Scoate din uz", alegi `Modalitatea iesirii din uz` (Casat, Vandut, Donat, Pierdut), `Data iesirii din uz` si urci documentul justificativ (proces-verbal de scoatere din functiune/declasare, factura de vanzare etc.). In tabel, coloana `In uz?` devine `Nu`, iar coloana `Justif.` arata documentul atasat; coloana `Data Modificare` arata ultima actualizare. Tabelul are si cautare pe coloane si paginare.

Registrul-inventar se descarca din pagina [Registre](#registre) (tab `Registru inventar`, iconitele CSV/XLSX), direct ca fisier CSV sau XLSX.


![inventar](readmepics/inventar.png)



## Registre

Aici ai o vedere de ansamblu asupra incasarilor, cheltuielilor precum si taxele/impozitele de platit pentru anul selectat, venituri vs cheltuieli pe ani, notificari facturi neincasate, declaratii de urcat in SPV etc. Totodata ai disponibile si registrele contabile obligatorii pe care trebuie sa le ai in relatia cu ANAF, in 5 taburi: `Registru jurnal`, `Registru fiscal`, `Registru inventar`, `Jurnal Cumparaturi` si `Jurnal Vanzari`.

Selectoarele de langa titlu aleg **anul** (doar anii cu inregistrari) si moneda de afisare (`In RON` / `In EUR`) pentru grafic si pentru toate cardurile. Cardurile arata total neincasate (cu `E ok 👍` daca nu ai), total incasari brut, total incasari net, total cheltuieli si, in a doua rand, total taxe/impozite, pensie (CAS), sanatate (CASS) si impozit pe venit. Sub titlu vezi si totalul platilor catre stat pe toti anii, totalul incasarilor nete pe toti anii si restul de plata.

Taxele se calculeaza pe regulile din anul selectat (vezi `src/utils/calcule.py`). Cei scutiti (profesii liberale cu casa de asigurari proprie, pensionari etc.) pot bifa scutirile in [Setari](#setari).

Toate calculele financiare se fac cu `Decimal` (vezi `src/utils/decimale.py`), pastrand toate zecimalele in calculele intermediare, fara rotunjiri. Sumele finale (totaluri, taxe de plata) se rotunjesc la 2 zecimale cu `rotund2` (`ROUND_HALF_UP`).

Poti descarca registrele dand click fie pe iconita de csv sau xlsx. Se descarca direct un singur fisier CSV sau XLSX cu datele registrului, fara arhiva zip si fara documentele justificative. Toate fisierele salvate in aplicatie vor avea un prefix id de 8 caractere dupa care le puteti gasi (ex: `0x4rf2KW_Factura_etc.pdf`).  

In tab-ul **Jurnal Cumparaturi** gasesti **Jurnalul de cumpărări**: daca ai cheltuieli cu servicii din UE/non-UE (taxare inversa), jurnalul pentru cumparari cu referinta `15-16`, baza impozitabila, TVA autolichidata si totalurile, descarcabil in CSV sau XLSX (pe luna sau pe tot anul).

In tab-ul **Jurnal Vanzari** gasesti facturile emise catre clienti `Client UE VIES`, cu valoarea in lei, data incasarii si documentul justificativ; acelasi jurnal e inclus si in zip-ul D390 descris mai sus.


![registre](readmepics/registre.png)


## Actualizare aplicatie

Versiunea pe care o rulezi apare in subsolul paginii `Setari` (ex. `PFASimplu V3.0.4`). Cand exista o versiune noua, langa ea apare `(disponibil V...)` impreuna cu un link catre [GitHub Releases](https://github.com/ClimenteA/PFASimplu/releases), de unde o poti descarca. Aplicatia nu descarca si nu instaleaza nimic automat.

**Actualizare executabil standalone:** descarca arhiva `.zip` pentru sistemul tau de operare, dezarhiveaza-o si ruleaza executabilul nou. Executabilul vechi poate fi sters: baza de date, documentele si celelalte date raman in directorul de date al sistemului (`%LOCALAPPDATA%\PFASimplu`, `~/Library/Application Support/PFASimplu` sau `~/.local/share/pfasimplu`), deci nu sunt afectate. Ca masura de precautie, inainte de upgrade copiaza acest director (backup) si fa un export al datelor din `Setari` → `Exporta datele din aplicatie`. Arhiva este descarcata prin HTTPS, dar binarul nu este semnat (vezi sectiunea de distributie standalone). Pentru Docker sau rulare din sursa folosesti procedura de mai jos.

**Actualizare locala (Docker / sursa):** fa `git pull`, reconstruieste imaginea si reporneste containerele. Baza de date si fisierele raman pe loc: sunt in `appdata/db/` si `appdata/files/` pe disc, nu in imagine.

```bash
git pull
docker compose -f docker-compose-local.yaml up -d --build
```

Daca update-ul schimba doar codul (fara `pyproject.toml`/`uv.lock`), rebuild-ul
nu e necesar: sursa e montata live, deci ajunge `make restart-local` (local)
sau `make restart` (VPS).

Pe VPS, folosesti `docker-compose.yaml`. Pentru siguranta, inainte de actualizare poti face un export pe an din `Setari` → `Exporta datele din aplicatie` (sau copiaza direct folderul `appdata/`).


## Debug si testare (dezvoltatori)

### Rulare in Docker pentru dezvoltare

```bash
make start-local        # http://localhost:8990 (fara Caddy), restart: unless-stopped
make restart-local      # dupa editari de cod: reincarca sursa, fara rebuild
make logs-local         # logurile aplicatiei
make stop-local

make start              # varianta cu Caddy (necesita .env.prod)
make restart            # echivalentul lui restart-local pentru VPS
```

Codul sursa e montat live in containere (`./src` la `/app/src`), deci dupa
modificari de cod e suficient `make restart-local` (respectiv `make restart` pe
VPS); waitress nu are auto-reload, asa ca containerul trebuie recreat.
`make build-local` / `make build` raman necesare doar cand se schimba
dependintele (`pyproject.toml`, `uv.lock`) sau `Dockerfile`-ul.

Aplicatia ruleaza in container cu `PFASIMPLU_DEBUG=0`. Pe HTTP (localhost)
cookie-urile `Secure` sunt dezactivate prin `PFASIMPLU_SECURE_COOKIES=0`,
altfel browserul nu ar trimite sesiunea de login. In spatele Caddy/HTTPS se
foloseste valoarea implicita (`1`).

Loginul e obligatoriu: creaza un cont la `/conturi/inregistrare/` sau un
superutilizator prin `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD`
in `.env` (local) ori `.env.prod` (VPS).

### Rulare cu uv run (dezvoltare)

Se poate lucra si direct din sursa, cu auto-reload, fara Docker. Loginul e
obligatoriu si aici:

```bash
uv sync                 # dependinte (grupul dev: pytest, playwright, faker, ruff)
make dev                # http://127.0.0.1:8990, cu auto-reload
make dev-e2e            # aplicatia pe baza de date generata de teste (test.db)
make dev-superuser      # optional, cont de admin pentru /admin/
make test-e2e           # teste end-to-end
make migrate-all        # regenerare migrari (daca ai modificat modelele)
```

`make dev` foloseste **aceeasi baza de date si acelasi folder media ca Docker-ul
local** (`appdata/db/stocare.db` si `appdata/files/`), deci datele se pastreaza
cand treci de la `make dev` la `make start-local`. Daca ambele ruleaza pe 8990,
opreste unul dintre ele sau schimba portul cu `make dev DEV_PORT=8991`.
Pe Windows: `.\makefile.bat dev` (si `dev-superuser`).

Variabile de mediu utile (`src/core/settings.py` si fisierele compose):

| Variabila | Rol | Implicit |
|---|---|---|
| `PFASIMPLU_DB_PATH` / `PFASIMPLU_DB_DIR` | locatia bazei de date SQLite (in Docker: `/data/db`, montat din `appdata/db/`) | `appdata/db/stocare.db` |
| `PFASIMPLU_MEDIA_ROOT` | folderul fisierelor urcate/generate (in Docker: `/data/files`, montat din `appdata/files/`) | `appdata/files/` |
| `PFASIMPLU_LOG_DIR` | folderul logurilor (in Docker: `/data/logs`, montat din `appdata/logs/`); fisierul e `pfasimplu.log`, cu rotatie la 5 MB | `appdata/logs/` |
| `PFASIMPLU_STATIC_ROOT` | folderul fisierelor statice colectate | `src/staticfiles/` |
| `PFASIMPLU_PORT` | portul aplicatiei in compose-ul local | `8990` |
| `PFASIMPLU_DEBUG` | `0` = mod productie (fara trace-uri in browser) | `1` |
| `PFASIMPLU_SECURE_COOKIES` | `0` = cookie-uri normale (HTTP local) | `1` cand `DEBUG=0` |
| `PFASIMPLU_ALLOW_REGISTRATION` | `0` = blocheaza crearea de conturi | `1` |
| `PFASIMPLU_SECRET_KEY`, `PFASIMPLU_ALLOWED_HOSTS`, `PFASIMPLU_CSRF_TRUSTED_ORIGINS` | necesare pe server (vezi `.env.prod.example`) | - |
| `PFASIMPLU_DOMAIN` | domeniul folosit de Caddy | `pfa.exemplu.ro` |

### Structura codului

Radacina repo-ului contine configuratia proiectului, documentatia si fisierele Docker. Codul aplicatiei sta in `src/`.

| Folder / fisier | Rol |
|---|---|
| `README.md` | documentatia aplicatiei (instalare, ghid de utilizare, depanare) |
| `GHID_PFA_SISTEM_REAL.md` | ghid legislativ: registre, declaratii, deductibilitati, TVA, cu trimiteri la actele normative |
| `src/` | sursele aplicatiei: app-urile Django, `core/`, `templates/`, `static/`, `tests/` |
| `appdata/` | datele locale: `db/stocare.db` (SQLite), `files/` (fisiere urcate/generate) si `logs/pfasimplu.log`; ignorate de git si montate in Docker |
| `Dockerfile`, `docker-entrypoint.sh` | imaginea aplicatiei (migrari + collectstatic la pornire) |
| `docker-compose.yaml` | varianta VPS: aplicatie + Caddy |
| `docker-compose-local.yaml` | varianta locala: aplicatie, fara Caddy |
| `Caddyfile`, `.env.prod.example` | configurare TLS/domeniu pentru VPS |
| `.env.example` / `.env` | configurare locala (mock, ignorata de git) |
| `readmepics/` | imagini folosite in acest README |

| App / folder (in `src/`) | Rol |
|---|---|
| `setari/` | datele PFA-ului, IBAN-uri, cod TVA intracomunitar, export/stergere date |
| `facturi/` | emitere facturi: PDF multi-limba + XML e-factura (UBL) |
| `incasari/` | incasari + documente justificative, conversie BNR, filtru UE si D390 pentru clienti UE |
| `cheltuieli/` | cheltuieli, deductibilitate, amortizare, taxare inversa TVA, D301/D390 pentru achizitii |
| `documente/` | arhiva ANAF (D212, dovezi plata, recipise D301/D390) cu parsing PDF |
| `inventar/` | obiecte de inventar si mijloace fixe, iesire din uz |
| `registre/` | dashboard + registrele contabile (inclusiv Jurnal Vanzari), exporturi CSV/XLSX |
| `conturi/` | login/inregistrare/logout (obligatorii) si izolarea datelor pe cont |
| `utils/` | calcule taxe (`calcule.py`), TVA si generare D301/D390 (`tva.py`, `tva_documente.py`), curs BNR (`valuta.py`), cautare/paginare/export (`views.py`), fisiere (`files.py`), PDF-uri (`mijloc_fix_pdf.py`) |
| `templates/` + `static/` | UI dark: PicoCSS + Alpine.js, typeahead; fara build step de frontend |
| `tests/` | teste end-to-end Playwright (vezi mai jos) |

### Teste end-to-end

Testele ruleaza un scenariu complet pe anul curent (Setari → Facturi → Incasari → Cheltuieli, inclusiv taxare inversa, clienti UE VIES si mijloace fixe) intr-un browser real, pe o **bază de date izolata** (`src/tests/.runtime/test.db`) - datele reale nu sunt atinse. Sunt acoperite si validarea codului TVA pentru clientii UE, autocompletarea clientilor salvati si generarea D390 pentru incasarile din UE. Detalii in [tests/README.md](src/tests/README.md).

```bash
make test-e2e           # instaleaza Chromium (daca lipseste) + ruleaza toate testele

# echivalent, cu optiuni:
uv run playwright install chromium          # o singura data
uv run pytest src/tests/ -v                     # headless
uv run pytest src/tests/ -v --headed --slowmo 300   # cu browser vizibil
uv run pytest src/tests/ -v -k "luna3"          # doar o luna / o etapa
```

Dupa rulare, baza de date de test ramane in `src/tests/.runtime/` pentru inspectie manuala (o poti deschide cu orice client SQLite sau rula aplicatia pe ea cu `make dev-e2e`). Logare: `test@pfasimplu.ro` / `parola-test-e2e-123`.

### Depanare

- **Serverul nu porneste / port ocupat**: portul aplicatiei e `PFASIMPLU_PORT` in `.env` (implicit 8990); dupa modificare, `docker compose -f docker-compose-local.yaml up -d`.
- **Erori de migrari dupa modificari de modele**: `make migrate-all`; daca migrarile sunt corupte, `make purge-migration-dirs` apoi `make migrate-all` (atenție: pe o baza de date existenta cu schema veche poate fi nevoie de `make purge-db`, care **sterge datele**).
- **Curs BNR indisponibil**: `cursvalutarbnr` ia cursurile online si le cache-uieste in folderul temporar al sistemului (`cache_cursvalutarbnr`); prima rulare necesita internet.
- **Fisiere lipsa dupa mutarea bazei de date**: fisierele sunt referite relativ la `PFASIMPLU_MEDIA_ROOT` - muta tot folderul `appdata/` odata cu baza de date.
- **Login nu functioneaza pe HTTP local**: verifica `PFASIMPLU_SECURE_COOKIES=0` in `.env` (cookie-urile `Secure` nu sunt trimise de browser pe `http://localhost`).
- **Datele nu se vad dupa rebuild**: sunt bind-mount-uite din `appdata/`; nu le stergi si nu le muta fara sa actualizezi compose-ul.
- **Loguri / erori de zi cu zi**: verifica `appdata/logs/pfasimplu.log` (in Docker: `/data/logs/pfasimplu.log`); se roteste la 5 MB, cu 3 copii vechi. `docker compose logs` arata doar iesirea consolei.
- **Eroare `env_file` lipseste**: copiaza `.env.example` in `.env` inainte de `docker compose`.


## Observatii

**Aplicatia este oferita ca atare, nu are nici o garantie asociata**. Nu imi asumam raspunderea pentru eventuale erori in procesare date contabilitate, daune provocate dispozitivelor etc. Testeaza aplicatia inainte si vezi daca raspunde nevoilor tale inainte de o adauga in rutina de lucru.

Daca gasesti erori in aplicatie poti deschide un [`New issue`](https://github.com/ClimenteA/PFASimplu/issues/new) in tabul `Issues` din acesta pagina.
