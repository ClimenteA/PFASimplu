# PFASimplu

Aplicatie contabilitate partida simpla pentru PFA. 


## Declaratii ANAF pentru PFA

Persoanele Fizice Autorizate (PFA) din România au obligația de a depune o serie de declarații fiscale și contabile. Iată care sunt acestea:

Declarația unică (212):

Aceasta este principala declarație fiscală pentru PFA-uri, în care se declară veniturile realizate și se calculează impozitul pe venit și contribuțiile sociale (CAS și CASS).
Se depune anual, de obicei până la 25 mai pentru veniturile realizate în anul anterior.
Declarația privind venitul estimat/norma de venit (212):

Se poate depune pentru estimarea veniturilor și a impozitelor pentru anul în curs.
Aceasta se depune la începutul activității sau în cazul în care se anticipează o schimbare semnificativă a veniturilor.
Declarația 600:

Aceasta a fost necesară până în 2018 pentru determinarea contribuțiilor sociale, dar a fost ulterior inclusă în Declarația unică (212).
Declarația 394:

Este o declarație informativă privind livrările/prestările și achizițiile efectuate pe teritoriul național.
Se depune trimestrial sau lunar, în funcție de perioada fiscală aleasă pentru TVA, dacă PFA-ul este plătitor de TVA.
Decontul de TVA (300):

Dacă PFA-ul este plătitor de TVA, acesta trebuie să depună decontul de TVA lunar sau trimestrial.
Declarația 390:

Este necesară pentru tranzacțiile intracomunitare.
Se depune lunar, în cazul în care PFA-ul realizează astfel de tranzacții.
Declarația 112:

Este o declarație privind obligațiile de plată ale contribuțiilor sociale, impozitului pe venit și evidența nominală a persoanelor asigurate.
Se depune lunar sau trimestrial, în funcție de cum alege PFA-ul să declare și să plătească contribuțiile sociale pentru angajați, dacă are salariați.
Pe lângă aceste declarații principale, există și alte obligații care pot apărea în funcție de specificul activității desfășurate:

Jurnalele de vânzări și cumpărări: Pentru PFA-urile plătitoare de TVA.
Registrul de evidență fiscală: În care se înregistrează veniturile și cheltuielile.
Declarații informative privind contractele de muncă: Dacă PFA-ul are angajați.
Este important ca fiecare PFA să se informeze periodic asupra legislației fiscale în vigoare și să consulte un contabil sau un specialist fiscal pentru a se asigura că toate obligațiile fiscale sunt îndeplinite corect și la timp.



# Development

This project is made in Typescript with HonoJS, Tailwind (Daisyui) and Sqlite. 
It uses Bunjs as a runtime because it can easily generate cross-platform binaries.

- clone repo;
- `bun install`;
- `bun run css` - for tailwind;
- `bun run browser` - for reloading webpage on each change;
- `bun run hot` - server reload;
- `bun run build`- to generate binary;
