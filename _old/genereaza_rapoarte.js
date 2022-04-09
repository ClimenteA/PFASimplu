// https://droces.github.io/Deno-Cheat-Sheet/
// ./deno run --allow-all genereaza_rapoarte.js


// Compile linux
// ./deno compile --output ../registrator/registrator_linux_x64 --target x86_64-unknown-linux-gnu --allow-read --allow-write main.js

// Compile windows
// ./deno compile --output ../registrator/registrator_windows_x64 --target x86_64-pc-windows-msvc --allow-read --allow-write main.js

// Compile mac
// ./deno compile --output ../registrator/registrator_mac_x64 --target x86_64-apple-darwin --allow-read --allow-write main.js


// Target OS architecture 
// Windows x64, macOS x64, macOS ARM and Linux x64.
// x86_64-pc-windows-msvc
// x86_64-apple-darwin
// aarch64-apple-darwin
// x86_64-unknown-linux-gnu 

// TODO: use objects instead of list with indexes every where 


import { creeazaFisierulIncasari } from "./creeaza_incasari.js"
import { creeazaFisierulCheltuieli } from "./creeaza_cheltuieli.js"
import { gatherPaths } from "./gather_paths.js"
import { creeazaRegistruJurnal } from "./registru_jurnal.js"
import { creeazaRegistruInventar } from "./registru_inventar.js"
import { creeazaRegistruFiscal } from "./registru_fiscal.js"
import { creeazaBoilerplateAnFiscal } from "./creeaza_boilerplate.js"
import { adaugaComisioaneBanca } from "./adauga_comisioane_banca.js"
import { adaugaAmortizariMijloaceFixe } from "./adauga_amortizari_mijloace_fixe.js"


export async function genereazaRapoarte() {

    await creeazaBoilerplateAnFiscal()

    let paths      = await gatherPaths(false)
    let incasari   = await creeazaFisierulIncasari(paths.incasari, false)
    let cheltuieli = await creeazaFisierulCheltuieli(paths.cheltuieli, false)
    let cheltuieli_plus_comisioane = await adaugaComisioaneBanca(paths.extrase_bancare, cheltuieli, false)
    let cheltuieli_plus_mijloace_fixe = await adaugaAmortizariMijloaceFixe(paths.fisa_mijloc_fix, cheltuieli_plus_comisioane, false)

    let registruJurnal = await creeazaRegistruJurnal({
        incasari: incasari,
        cheltuieli: cheltuieli_plus_mijloace_fixe
    }, false)

    let registruInventar = await creeazaRegistruInventar(registruJurnal, false)
    let registruFiscal = await creeazaRegistruFiscal(registruJurnal, false)

    return {
        registruJurnal: registruJurnal,
        registruInventar: registruInventar,
        registruFiscal: registruFiscal
    }

}


// await genereazaRapoarte()
