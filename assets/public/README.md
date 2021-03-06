## Cine poate folosi aplicatia?
Aplicatia poate fi utila pentru oricine:
- tine contabilitatea in partida simpla;
- cu sistem de venit real;
- este neplatitor de TVA;
- nu are angajati; 



## Facilitati 

- Adaugare incasari (inregistrare facturi emise);
- Adaugare cheltuieli deductibile (inregistrare facturi/bonuri/extrase bancare);
- Generare automata a urmatoarelor registre contabile:
    - Registru Jurnal;
    - Registru Inventar; 
    - Registru Fiscal;
    - Fisa Mijloc Fix;
- Download CSV registre;
- Generare factura in format PDF;

Calcul automat impozite pentru declaratia unica (CAS/CASS/Impozit):
- Calcul Venit Net: `venitNet = totalIncasari - totalCheltuieli`;
- Calcul Impozit pe Venit: `impozitPeVenit = 10% din venitNet`;
- Calcul CAS (Pensie): 
    * `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` mai mare de 12 salarii minime brute pana in anul 2022 inclusiv;
    * `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` intre 12 si 24 salarii minime brute din anul 2023+;
    * `bazaDeCalculCAS = salariuMinimBrut x 24` - daca `venitNet` mai mare de 24 salarii minime brute din anul 2023+;
    * `CAS = 25% din bazaDeCalculCAS`;
- Calcul CASS (Sanatate):
    * `bazaDeCalculCASS = salariuMinimBrut x 12` - daca `venitNet` mai mare de 12 salarii minime brute pana in anul 2022 inclusiv;
    * `bazaDeCalculCASS = salariuMinimBrut x 6` - daca `venitNet` mai mare de 6 salarii minime brute din anul 2023+;
    * `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` intre 12 si 24 salarii minime brute din anul 2023+;
    * `bazaDeCalculCAS = salariuMinimBrut x 24` - daca `venitNet` mai mare de 24 salarii minime brute din anul 2023+;
    * `CASS = 10% din bazaDeCalculCASS`;


Extra calcule:
- Total Profit Anual : daca ai adaugat soldul intermediar (suma cu care ai ramas pe card la sfarsit de an), se scade ce a mai ramas de plata catre stat si rezulta profitul anual;
- Procent Profit Anual : daca ai adaugat soldul intermediar, se calculeaza cat la suta reprezinta profitul anual din total incasari brut.

Rapoarte suplimentare:
- Tabel incasari - unde poti vedea/sterge incasarile;
- Tabel cheltuieli - unde poti vedea/sterge cheltuielile;
- Tabel declaratii - unde poti vedea/sterge declaratiile;
- Grafic tip `bar chart` cu incasari vs cheltuieli pe luni;



# Tutorial Aplicatie

<!-- TOC -->

1. [Cum rulezi aplicatia](#cum-rulezi-aplicatia)
2. [Creeare cont](#creeare-cont)
3. [Adaugare incasari](#adaugare-incasari)
4. [Adaugare cheltuieli](#adaugare-cheltuieli)
5. [Adaugare documente](#adaugare-documente)
6. [Adauga sold intermediar](#adaugare-sold-intermediar)
7. [Creeaza o factura](#creeaza-factura)
8. [Registre contabile](#registre-contabile)
9. [Setari avansate](#setari-avansate)
10. [Observatii](#observatii)
11. [Pe viitor](#pe-viitor)



<!-- /TOC -->

<a name="cum-rulezi-aplicatia"></a>
## Cum rulezi aplicatia

1. Download executabil pentru sistemul dvs de operare:
- [Download PFASimplu-Windows-64bit](https://github.com/ClimenteA/PFASimplu/releases/tag/v.0.0.0);
- [Download PFASimplu-MacOS-64bit](https://github.com/ClimenteA/PFASimplu/releases/tag/v.0.0.0);
- [Download PFASimplu-Linux-64bit](https://github.com/ClimenteA/PFASimplu/releases/tag/v.0.0.0);

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

Pornire aplicatie din codul sursa:
- [clone github repo](https://github.com/ClimenteA/PFASimplu);
- Deschide un terminal si tasteaza `make run` apoi apasa enter;
- aplicatia este facuta in limbajul [GO](https://go.dev/) cu web framework-ul [Fiber](https://docs.gofiber.io/);



<a name="creeare-cont"></a>
## Creeare cont

- click pe `Intra in cont`;
- click pe `Nu am un cont creat`;
- creaza contul cu email si parola;
- apoi intra in cont cu emailul si parola introdusa la creare cont;

Vei vedea langa executabil un nou folder `stocare` aici se vor salva doate datele introduse. 
Ai grija de folderul `stocare` pastreaza-l in 2 locatii pentru a nu pierde datele.


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
## Adaugare documente

- click pe `Adauga declaratii/documente`;
- completeaza campurile din formular;
- click pe `Choose File` si incarca factura pe care ai trimis-o catre client (pe telefon ai optiunea de a face poza la document);
- daca ai selectat `Dovada plata impozite` ca tip document 2 campuri in plus vor mai aparea de completat: `Suma Platita catre ANAF` si `Plata pentru anul` - aceste campuri sunt folosite pentru a calcula cat mai ai de platit catre stat;
- In campul `Plata pentru anul` trebuie completat anul pentru care a fost facuta plata catre stat - pentru fiecare an data scadenta pentru datoriile catre stat este pe 25 mai anul viitor celui curent (ex: anul 2021 a trecut si la noua declaratie revizuita pentru anul 2021 a mai ramas ceva de plata, atunci documentul care dovedeste restul de plata pentru anul 2021 va fi adaugat pentru anul 2021 desi anul curent este 2022);
- click pe `Adauga`;


Factura va fi salvata in folderul `stocare`. 
Poti oricand daca ai gresit sa stergi factura din pagina `Vezi registre contabile`. 


<a name="adaugare-sold-intermediar"></a>
## Adauga sold intermediar

- click pe `Adauga sold intermediar`;
- completeaza campurile din formular;

In orice extras bancar sau aplicatie bancara vei avea disponibila soldul/suma curenta.
Odata completat acest formular vei putea vedea cat profit ai realizat dupa toate cheltuielile facute. 


<a name="creeaza-factura"></a>
## Creeaza o factura

- click pe `Creeaza o factura`;
- completeaza campurile cerute (o parte din campuri vor fi completate automat pentru facturile viitoare);
- click pe `Adauga livrabil` pentru a adauga un produs/serviciu;
- click pe `Genereaza factura`;
- factura in format pdf va fi creata;

Creearea de facturi nu se face doar prin aceasta pagina poti folosi Google Docs pentru o factura mai personalizata pentru tine care mai apoi o poti adauga in pagina `Adauga incasari`.

Daca esti platitor de TVA poti adauga inca o linie pentru produse/servicii (apasa `Adauga livrabil`) unde completezi valoarea TVA.


<a name="registre-contabile"></a>
## Registre contabile

- click pe `Vezi registre contabile`;
- selecteaza rapoartele pentru anul dorit;
- vezi informatiile calculate automat din datele introduse anterior;
- download documente introduse;
- download tabele in format CSV;



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

- posibilitate adaugare `bazaDeCalcul` pentru cei care au norma de venit;
- generare model completare Declaratie 212; 
- adaugare TVA in calcul (avertizare depasire prag TVA);
- declaratie pentru TVA;
- modificare setari anuale (salariul minim pentru anul in curs, prag minim, tabel amortizare mijloc fix);
- one-click update app; 
- verificare aplicatie facuta de un specialist contabil;

Daca programul iti este si tie folositor, **[nu ezita sa faci o donatie!](https://www.buymeacoffee.com/climentea)**. Donatiile ma vor ajuta sa mentin acest mic proiect "in viata". 


**Daca ai observat orice greseala poti deschide un [issue pe github](https://github.com/ClimenteA/PFASimplu) sau o poti seziza in [mesajul pentru donatii](https://www.buymeacoffee.com/climentea).**

