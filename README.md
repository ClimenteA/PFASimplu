# PFASimplu


## Descriere aplicatie 

Aplicatia PFASimplu este utila pentru persoanele care isi tin contabilitatea in partida simpla.
Este foarte simplu de folosit, poate fi rulata de pe un stick. 
Aplicatia este de tip website asa ca poate fi accesata chiar si de pe un telefon aflat in aceeasi retea wifi (aplicatia trebuie sa ruleze pe un laptop/pc pentru asta). Acest lucru este folositor pentru adaugarea de bonuri/facturi care trebuie pozate.


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
- Prag CAS/CASS PFA/II/s.a pentru sistem norma de venit: cauta pe google: `Normele anuale de venit pe anul 2022` - `pragCasCass` va fi cel pentru CAEN-ul/localitatea ta;
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


## De adaugat pe viitor
- posibilitate adaugare `pragCasCass` pentru cei care au norma de venit;
- generare model completare Declaratie 212; 
- adaugare TVA in calcul (avertizare depasire prag TVA);
- audit facut de un specialist contabil;


## Observatii
**Aplicatia va este oferita ca atare, nu are nici o garantie asociata.** 
Nu ne asumam raspunderea pentru eventuale erori in procesare date contabilitate, daune provocate dispozitivelor dvs.
Testati aplicatia inainte si vedeti daca raspunde nevoilor dvs. inainte de o adauga in rutina de lucru. 