<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [PFASimplu](#pfasimplu)
  - [Descriere](#descriere)
  - [Cine poate folosi aplicatia?](#cine-poate-folosi-aplicatia)
  - [Facilitati](#facilitati)
  - [Cum rulezi aplicatia](#cum-rulezi-aplicatia)
  - [Creeare cont](#creeare-cont)
  - [Adaugare incasari](#adaugare-incasari)
  - [Adaugare cheltuieli](#adaugare-cheltuieli)
  - [Adaugare declaratii/documente](#adaugare-declaratiidocumente)
  - [Creeaza o factura](#creeaza-o-factura)
  - [Registre contabile](#registre-contabile)
  - [Scoate din inventar obiecte/mijloce fixe](#scoate-din-inventar-obiectemijloce-fixe)
  - [Setari avansate](#setari-avansate)
  - [Observatii](#observatii)
  - [Pe viitor](#pe-viitor)
- [Curs programare](#curs-programare)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# PFASimplu 
![GitHub all releases](https://img.shields.io/github/downloads/ClimenteA/PFASimplu/total?label=descarcari&style=for-the-badge)

Aplicatie pentru simplificarea gestiunii contabilitatii facuta in partida simpla.

[Click aici pentru articol cu cateva capturi de ecran](https://climente-alin.medium.com/pfasimplu-aplicatie-pentru-pfa-gratis-1ab24ad3c179)

[Click aici pentru tutorial video pe youtube](https://www.youtube.com/watch?v=2X7zV_-A3oU)


## Descriere 

Aplicatia PFASimplu este utila pentru persoanele care isi tin contabilitatea in partida simpla.
Este foarte simplu de folosit, poate fi rulata de pe un stick. 
Aplicatia este de tip website asa ca poate fi accesata chiar si de pe un telefon aflat in aceeasi retea wifi (aplicatia trebuie sa ruleze pe un laptop/pc pentru asta). Acest lucru este folositor pentru adaugarea de bonuri/facturi care trebuie pozate.


## Cine poate folosi aplicatia?
Aplicatia poate fi utila pentru oricine:
- tine contabilitatea in partida simpla cu sistem de venit real;
- este neplatitor de TVA (daca castigi sub 5000 EUR in fiecare luna e ok);
- nu are angajati (mai bine un SRL pentru asta); 



## Facilitati 

- Adaugare incasari (inregistrare facturi emise);
- Adaugare cheltuieli deductibile (inregistrare facturi/bonuri/extrase bancare);
- Generare automata a urmatoarelor registre contabile:
    - Registru Jurnal;
    - Registru Inventar; 
    - Registru Fiscal;
    - Fisa Mijloc Fix;
- Descarca registre contabile in format CSV (pentru Microsoft Excel/Libre Office/Google Sheets etc);

Rapoarte suplimentare:
- Tabel incasari - unde poti vedea/sterge incasarile;
- Tabel cheltuieli - unde poti vedea/sterge cheltuielile;
- Tabel declaratii - unde poti vedea/sterge declaratiile;
- Grafic tip `bar chart` cu incasari vs cheltuieli pe luni;

Cum se realizeaza calculul:

```go

ProcentCAS          = 25 // % Pensie
ProcentCASS         = 10 // % Sanatate
ProcentImpozitVenit = 10 // % Impozit pe venit


plafon6 = salariuMinimBrut * 6
plafon12 = salariuMinimBrut * 12
plafon24 = salariuMinimBrut * 24
plafon60 = salariuMinimBrut * 60

DACA anulCurrent <= 2022 {

    DACA venitNet > plafon12 {
        CAS = ProcentCAS * plafon12 / 100
        CASS = ProcentCASS * plafon12 / 100
    }

    impozitPeVenit = ProcentImpozitVenit * (venitNet - CAS) / 100

}

DACA anulCurrent == 2023 {

    DACA venitNet > plafon6 {
        CASS = ProcentCASS * plafon6 / 100
    }

    DACA venitNet > plafon12 && venitNet <= plafon24 {
        CAS = ProcentCAS * plafon12 / 100
        CASS = ProcentCASS * plafon12 / 100
    }

    DACA venitNet > plafon24 {
        CAS = ProcentCAS * plafon24 / 100
        CASS = ProcentCASS * plafon24 / 100
    }

    impozitPeVenit = ProcentImpozitVenit * (venitNet - CAS) / 100
}

DACA anulCurrent >= 2024 {

    DACA venitNet <= plafon6 {
        CASS = ProcentCASS * plafon6 / 100
    }

    DACA venitNet > plafon12 && venitNet <= plafon24 {
        CAS = ProcentCAS * plafon12 / 100
        CASS = ProcentCASS * plafon12 / 100
    }

    DACA venitNet > plafon24 {
        CAS = ProcentCAS * plafon24 / 100
        CASS = ProcentCASS * plafon24 / 100
    }

    DACA venitNet > plafon60 {
        CASS = ProcentCASS * plafon60 / 100
    }

    impozitPeVenit = ProcentImpozitVenit * (venitNet - CAS - CASS) / 100

}

total = CAS + CASS + impozitPeVenit

PlatiStat{
    CASPensie:    CAS,
    CASSSanatate: CASS,
    ImpozitVenit: impozitPeVenit,
    Total:        total,
}

```


<a name="cum-rulezi-aplicatia"></a>
## Cum rulezi aplicatia

1. Descarca executabil pentru sistemul dvs de operare:
- [Descarca PFASimplu-Windows-64bit](https://github.com/ClimenteA/PFASimplu/releases);
- [Descarca PFASimplu-MacOS-64bit](https://github.com/ClimenteA/PFASimplu/releases);
- [Descarca PFASimplu-Linux-64bit](https://github.com/ClimenteA/PFASimplu/releases);

2. Extrage-ti zip-ul pe un stick sau in pc/laptop;
3. Deschide-ti fisierul `INSTRUCTIUNI.txt` si urmati pasii de acolo;

Pentru Windows trebuie doar sa dati dublu click pe `pfasimplu.exe` si se va deschide un terminal cu urmatoare date (similare):

```

Aplicatia PFASimplu vX.X.X!
Pastreaza aceasta fereastra deschisa cat timp folosesti aplicatia!


Poti vedea aplicatia in browser la addresa:
http://localhost:3000 (pe acest dispozitiv)

Sau poti intra de pe telefon/tableta/laptop in browser pe addresa:
http://192.168.1.7:3000

```

Acum poti deschide aplicatia intr-un browser pe pc/laptop la adresa `http://localhost:3000` sau de pe browser dintr-un telefon aflat in aceeeasi retea wifi la adresa `http://192.168.1.7:3000` (adresa ta poate fi diferita).

Aplicatia este facuta in limbajul [GO](https://go.dev/) cu web framework-ul [Fiber](https://docs.gofiber.io/);


<a name="creeare-cont"></a>
## Creeare cont

- click pe `Intra in cont`;
- click pe `Nu am un cont creat`;
- creaza contul cu email si parola;
- apoi intra in cont cu emailul si parola introdusa la creare cont;

Vei vedea langa executabil un nou folder `stocare` aici se vor salva doate datele introduse. 
Ai grija de folderul `stocare` pastreaza-l in 2 locatii pentru a nu pierde datele.
Contul este creat doar in PC-ul/Laptopul tau, datele personale nu se transmit nicaieri (programul functioneaza si fara conexiune la internet).


<a name="adaugare-incasari"></a>
## Adaugare incasari

- click pe `Adauga incasari`;
- completeaza campurile din formular (o parte din campuri vor fi completate automat);
- click pe `Choose File` si incarca factura pe care ai trimis-o catre client (pe telefon ai optiunea de a face poza la factura);
- click pe `Adauga`;

Factura va fi salvata in folderul `stocare`. 
Poti oricand daca ai gresit sa stergi factura fie din pagina `Adauga incasari` fie din pagina `Vezi registre contabile`. 


<a name="adaugare-cheltuieli"></a>
## Adaugare cheltuieli

- click pe `Adauga cheltuieli`;
- completeaza campurile din formular;
- click pe `Choose File` si incarca factura pe care ai trimis-o catre client (pe telefon ai optiunea de a face poza la factura);
- daca `Suma cheltuita (RON)` depaseste pragul pentru obiect de inventar si atinge suma de mijloc fix atunci vor aparea mai multe campuri de completat precum si `Tabelele de amortizare mijloace fixe` sub formularul de cheltuieli;
- completeaza campurile aditionale pentru mijloc fix (`Cod clasificare`, `Amortizare in ani` `Data punerii in functiune`, `Data factura/bon/extras`) dupa ce ai consultat tabelele de amortizare mijloc fix (**Atentie: Cod clasificare trebuie pus complet! Ex: 3.4.2.**)
- daca nu este cazul unui mijloc fix si doar ai achizitionat consumabile de suma respectiva atunci debifeaza `Mijloc fix amortizabil`;
- click pe `Adauga`;

Bonul/Factura va fi salvata in folderul `stocare`. 
Poti oricand daca ai gresit sa stergi documentul fie din pagina `Adauga cheltuieli` fie din pagina `Vezi registre contabile`. 



<a name="adaugare-documente"></a>
## Adaugare declaratii/documente

- click pe `Adauga declaratii/documente`;
- completeaza campurile din formular;
- click pe `Choose File` si incarca factura pe care ai trimis-o catre client (pe telefon ai optiunea de a face poza la document);
- daca ai selectat `Declaratie unica (212)` ca tip document va mai aparea un camp `Declaratie pentru anul` aici poti trece anul pentru care adaugi declaratia. Declaratia poate fi pentru anul curent sau poate fi o declaratie rectificativa pentru anul anterior. Aceleasi reguli sunt valabile si pentru optiunile: `Dovada incarcare Declaratie 212` si `Dovada plata impozite`;
- daca ai selectat `Dovada plata impozite` ca tip document 2 campuri in plus vor mai aparea de completat: `Suma Platita catre ANAF` si `Plata pentru anul` - aceste campuri sunt folosite pentru a calcula cat mai ai de platit catre stat. In campul `Plata pentru anul` trebuie completat anul pentru care a fost facuta plata catre stat - pentru fiecare an data scadenta pentru datoriile catre stat este pe 25 mai anul viitor celui curent (ex: anul 2021 a trecut si la noua declaratie revizuita pentru anul 2021 a mai ramas ceva de plata, atunci documentul care dovedeste restul de plata pentru anul 2021 va fi adaugat pentru anul 2021 desi anul curent este 2022);
- click pe `Adauga`;

Factura va fi salvata in folderul `stocare`. 
Poti oricand daca ai gresit sa stergi factura din pagina `Vezi registre contabile`. 


<a name="creeaza-factura"></a>
## Creeaza o factura

[Tutorial pe facturis-online cum poti emite facturi folosind tool-urile ANAF](https://facturis-online.ro/e-factura/cum-sa-emiteti-singur-facturi-electronice-in-sistemul-anaf-ro-e-factura.html)


- [Completezi factura online si descarci fisierul XML aici](https://www.anaf.ro/CompletareFactura/faces/factura/informatiigenerale.xhtml);
- [Transformi fisierul XML in fisier PDF aici](https://www.anaf.ro/uploadxml/);
- Incarci fiserul XML in SPV: `Factura electronica` > `Trimitere Factura` > `Trimitere XML factura`;
- Creeaza un zip cu fisierele XML si PDF generate anterior si adauga-l in sectiunea `Adauga incasari`;


[ANAF informatii e-factura aici](https://mfinante.gov.ro/web/efactura/acasa)


<a name="registre-contabile"></a>
## Registre contabile

- click pe `Vezi registre contabile`;
- selecteaza rapoartele pentru anul dorit;
- vezi informatiile calculate automat din datele introduse anterior;
- descarca documente introduse;
- descarca tabele in format CSV;


<a name="scoate-din-inventar"></a>
## Scoate din inventar obiecte/mijloce fixe

Daca un obiect de inventar sau mijloc fix adaugat anterior in sectiunea `Adauga cheltuieli` nu mai poate fi folosit sau l-ai vandut in sectiunea `Scoate din inventar obiecte/mijloce fixe` putem inregistra aceasta operatie.

- selecteaza obiectul de inventar/mijloc fix din lista campul `Obiect/Mijloc Fix din Registru Inventar`;
- selecteaza `Tip operatiune` - `CASARE` sau `VANZARE`;
- pune data iesirii din uz (data casarii/vanzarii);
- adauga documentul care dovedeste ca obiectul a fost casat/vandut;
- click pe scoate;



<a name="setari-avansate"></a>
## Setari avansate

Sunt niste date care stau la baza calculelor si care se pot schimba de la an la an.

Aceste date sunt:
- salariul minim brut (se schimba anual);
- prag mijlox fix (se schimba foarte rar);
- tabel amortizare mijloace fixe (se schimba foarte rar);

O data pe an se recomanda un update al aplicatiei. Asta inseamna doar inlocuirea folderului `assets` si a executabilului `pfasimplu.exe` cu cele din zip-ul descarcat. 


Poti modifica aceste date si fara a descarca noua versiune. Pentru a face asta trebuie doar sa adaugi valorile necesare in fisierele din folderul `assets/public`:

- `salariul minim brut` si `prag mijlox fix` se pot schimba in fisierul `assets/public/pfaconfig.json`;
- `tabel amortizare mijloace fixe` se pot schimba in fisierul `assets/public/lista_coduri_mijloace_fixe.json`;




<a name="observatii"></a>
## Observatii

**Aplicatia va este oferita ca atare, nu are nici o garantie asociata.** 
Nu ne asumam raspunderea pentru eventuale erori in procesare date contabilitate, daune provocate dispozitivelor dvs.
Testati aplicatia inainte si vedeti daca raspunde nevoilor dvs. inainte de o adauga in rutina de lucru. 


<a name="pe-viitor"></a>
## Pe viitor

- e-factura;
- modificare setari anuale (salariul minim pentru anul in curs, prag minim, tabel amortizare mijloc fix);
- one-click update app; 
- verificare aplicatie facuta de un specialist contabil;

**Daca ai observat orice greseala sau ai o intrebare poti deschide un [issue pe github](https://github.com/ClimenteA/PFASimplu) sau poti intra pe reddit grupul [r/PFASimplu](https://www.reddit.com/r/PFASimplu/).**


<a name="curs-programare"></a>
# Curs programare

Daca esti interesat(a) sa inveti programare (web development) pentru a face aplicatii software pentru afacerea ta sau vrei sa faci o reconversie profesionala (web: frontend, backend, devops, testare) [**click aici**](https://curs.softgata.com/crs/landing).
