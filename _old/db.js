import Datastore from "https://deno.land/x/dndb@0.3.3/mod.ts"


export const ultimaIncasareDB = new Datastore({ filename: "../ANAF/db/ultima_incasare.json", autoload: true })
export const incasariDB = new Datastore({ filename: "../ANAF/db/incasari.json", autoload: true })
export const cheltuieliDB = new Datastore({ filename: "../ANAF/db/cheltuieli.json", autoload: true })
export const furnizorDB = new Datastore({ filename: "../ANAF/db/furnizor.json", autoload: true })
export const clientiDB = new Datastore({ filename: "../ANAF/db/clienti.json", autoload: true })
