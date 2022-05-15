# PFASimplu

Aplicatie pentru simplificarea gestiunii contabilitatii facuta in partida simpla.

## Descriere 

Aplicatia PFASimplu este utila pentru persoanele care isi tin contabilitatea in partida simpla.
Este foarte simplu de folosit, poate fi rulata de pe un stick. 
Aplicatia este de tip website asa ca poate fi accesata chiar si de pe un telefon aflat in aceeasi retea wifi (aplicatia trebuie sa ruleze pe un laptop/pc pentru asta). Acest lucru este folositor pentru adaugarea de bonuri/facturi care trebuie pozate.


## Cine poate folosi aplicatia?
Aplicatia poate fi utila pentru oricine tine contabilitatea in partida simpla cu sistem de venit real, neplatitor de TVA.


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
- Prag CAS/CASS PFA/II/s.a pentru sistem real: `pragCasCass = salariul_minim_pe_anul_in_curs * 12`;
- Prag CAS/CASS PFA/II/s.a pentru sistem norma de venit: cauta pe google: `Normele anuale de venit pe anul 20XX` - `pragCasCass` va fi cel pentru CAEN-ul/localitatea ta;
- Venit net: `venitNet = Total incasari - Total cheltuieli`;
- Calcul CAS (Pensie): 25% din `venitNet` daca `venitNet` > (mai mare ca) `pragCasCass`;
- Calcul CASS (Sanatate): 10% din `venitNet` daca `venitNet` > (mai mare ca) `pragCasCass`;
- Impozit pe venit : 10% din (incasari - cheltuieli - CAS) - impozitul pe venit nu este deductibil.

Extra calcule:
- Total Profit Anual : daca ai adaugat soldul intermediar (suma cu care ai ramas pe card la sfarsit de an), se scade ce a mai ramas de plata catre stat si rezulta profitul anual;
- Procent Profit Anual : daca ai adaugat soldul intermediar, se calculeaza cat la suta reprezinta profitul anual din total incasari brut.

Rapoarte suplimentare:
- Tabel incasari - unde poti vedea/sterge incasarile;
- Tabel cheltuieli - unde poti vedea/sterge cheltuielile;
- Tabel declaratii - unde poti vedea/sterge declaratiile;
- Grafic tip `bar chart` cu incasari vs cheltuieli pe luni;



# Tutorial Aplicatie PFASimplu

<!-- TOC -->

1. [Cum rulezi aplicatia](#cum-rulezi-aplicatia)
2. [Creeare cont](#creeare-cont)
3. [Adaugare incasari](#adaugare-incasari)
4. [Adaugare cheltuieli](#adaugare-cheltuieli)
5. [Adaugare documente](#adaugare-documente)
6. [Registre contabile](#registre-contabile)

<!-- /TOC -->

<a name="cum-rulezi-aplicatia"></a>
## Cum rulezi aplicatia

1. Download executabil pentru sistemul dvs de operare:
- [Download PFASimplu-Windows-64bit](TODOLINK);
- [Download PFASimplu-MacOS-64bit](TODOLINK);
- [Download PFASimplu-Linux-64bit](TODOLINK);

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
- clic pe `Nu am un cont creat`;
- creaza contul cu email si parola;
- apoi intra in cont cu emailul si parola introdusa la creare cont;

Vei vedea langa executabil un nou folder `stocare` aici se vor salva doate datele introduse. 
Ai grija de folderul `stocare` pastreaza-l in 2 locatii pentru a nu pierde datele.


<a name="adaugare-incasari"></a>
## Adaugare incasari


<a name="adaugare-cheltuieli"></a>
## Adaugare cheltuieli


<a name="adaugare-documente"></a>
## Adaugare documente


<a name="registre-contabile"></a>
## Registre contabile





## De adaugat pe viitor
- posibilitate adaugare `pragCasCass` pentru cei care au norma de venit;
- generare model completare Declaratie 212; 
- adaugare TVA in calcul (avertizare depasire prag TVA);
- audit facut de un specialist contabil;



## Observatii
**Aplicatia va este oferita ca atare, nu are nici o garantie asociata.** 
Nu ne asumam raspunderea pentru eventuale erori in procesare date contabilitate, daune provocate dispozitivelor dvs.
Testati aplicatia inainte si vedeti daca raspunde nevoilor dvs. inainte de o adauga in rutina de lucru. 



