import { basePath } from "./config.js"
import {exists} from "https://deno.land/std/fs/mod.ts"



export async function creeazaBoilerplateAnFiscal(){


    let an = String(new Date().getFullYear())

    if (!await exists(basePath)) {
        await Deno.mkdir(basePath)
    }

    let path = basePath + '/' + "An fiscal " + an
    
    if (!await exists(path)) {
        
        await Deno.mkdir(path)

        let anafPath = path + "/ANAF Declaratii"
        await Deno.mkdir(anafPath)

        let cheltuieliPath = path + "/Cheltuieli"
        await Deno.mkdir(cheltuieliPath)

        let incasariPath = path + "/Incasari"
        await Deno.mkdir(incasariPath)

        // let cheltuieliFileName = an + "-01-01 0 RON 0 achizitii.jpg"
        // let incasariFileName = "Factura " + an + "-01-01 XX XX 0 RON.pdf"

        // let fc = await Deno.open(cheltuieliPath + "/" + cheltuieliFileName, { write: true, create: true })
        // fc.close()

        // let fa = await Deno.open(incasariPath + "/" + incasariFileName, { write: true, create: true })
        // fa.close()
    }

}

