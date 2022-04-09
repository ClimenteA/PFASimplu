import { basePath } from "./config.js"



export async function gatherPaths(showLogs) {

    // Preia din folderul ANAF path-ul catre fisierele corespunzatoare pentru Incasari, Cheltuieli si Extrasul bancar

    let incasari = {}
    let cheltuieli = {}
    let extrase_bancare = {}
    let fisa_mijloc_fix = {}

    for await (let dir of Deno.readDir(basePath)) {
        if (dir.isFile) continue
        for await (let anFiscal of Deno.readDir(basePath + '/' + dir.name)) {

            if (anFiscal.name == "Incasari") {
                
                if (incasari[dir.name] == undefined) incasari[dir.name] = []
                
                let incasariPath = basePath + '/' + dir.name + '/' + "Incasari"
                
                for await (let file of Deno.readDir(incasariPath)) {
                    if (file.name.endsWith('.pdf') || file.name.endsWith('.jpg')) {
                        incasari[dir.name].push(incasariPath + '/' + file.name)
                    }
                }
            }

            else if (anFiscal.name == "Cheltuieli") {
                
                if (cheltuieli[dir.name] == undefined) cheltuieli[dir.name] = []
                if (extrase_bancare[dir.name] == undefined) extrase_bancare[dir.name] = []
                if (fisa_mijloc_fix[dir.name] == undefined) fisa_mijloc_fix[dir.name] = []

                
                let cheltuieliPath = basePath + '/' + dir.name + '/' + "Cheltuieli"
                
                for await (let file of Deno.readDir(cheltuieliPath)) {
                    
                    if (file.name.startsWith("FMF")){
                        fisa_mijloc_fix[dir.name].push(cheltuieliPath + '/' + file.name)
                    }

                    else if (file.name.endsWith('.pdf') || file.name.endsWith('.jpg')) {
                        cheltuieli[dir.name].push(cheltuieliPath + '/' + file.name)
                    }
                
                    else if (file.name.endsWith('istoric_bancar_ing.csv')) {
                        extrase_bancare[dir.name].push(cheltuieliPath + '/' + file.name)
                    }
                }
            }
        }

    }

    let paths = {
        incasari: incasari, 
        cheltuieli: cheltuieli, 
        extrase_bancare: extrase_bancare,
        fisa_mijloc_fix: fisa_mijloc_fix
    }

    if (showLogs) console.log("Fisiere incasari/cheltuieli/extrase/mijloacefixe:", paths)

    return paths

}
