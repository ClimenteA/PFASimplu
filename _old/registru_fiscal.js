import { basePath } from "./config.js"
import { writeCSV } from "https://deno.land/x/csv/mod.ts"


function groupByYear(registruJurnal){

    let groupedByYear = {}
    for (let li of registruJurnal.slice(1)) {

        // Skip calcul total
        if (li[0] == '-') continue

        let an

        if (li[2].startsWith('Anul ')) {
            an = li[2].split(' ')[1]
        } else {
            an = li[2].split("/")[2].split(" ").at(-1) // get year from file path
        }

        if (!(an in groupedByYear)) groupedByYear[an] = []

        groupedByYear[an].push(li)

    }

    return groupedByYear

}


export async function creeazaRegistruFiscal(registruJurnal, showLogs) {

    // exemplu li
    // [
    //     23,
    //     "2022-01-04",
    //     "../ANAF/An fiscal 2021/Cheltuieli/2022-01-04 16.95 RON Transport  numerar.jpg",
    //     "Achizitie Transport  numerar",
    //     0,
    //     0,
    //     16.95,
    //     0
    // ]
    
    let rows = [
        [
            "Nr.Crt.",
            "Elemente de calcul pentru stabilirea venitului net annual/pierderii nete anuale",
            "Valoare (RON)",
            "Anul"
        ]
    ]

    let dataGroupedli = groupByYear(registruJurnal)
    
    let nrCrt = 0
    for (let key in dataGroupedli) {

        let totalIncasari = 0
        let totalPlati = 0

        for (let li of dataGroupedli[key]){
            // console.log(li)
            totalIncasari = li[4] + li[5] + totalIncasari
            totalPlati = li[6] + li[7] + totalPlati
        }

        nrCrt = nrCrt + 1
        
        let rowIncasari = [
            nrCrt, // Nr.Crt.
            "Total incasari", // Elemente de calcul
            totalIncasari.toFixed(2), // Valoare
            key // Anul
        ]

        nrCrt = nrCrt + 1

        let rowCheltuieli = [
            nrCrt, // Nr.Crt.
            "Total cheltuieli", // Elemente de calcul
            totalPlati.toFixed(2), // Valoare
            key // Anul
        ]

        rows.push(rowIncasari)
        rows.push(rowCheltuieli)

    }

    const csvPath = basePath + "/" + "Registru Fiscal.csv"
    const f = await Deno.open(csvPath, { write: true, create: true, truncate: true })
    await writeCSV(f, rows)
    f.close()

    if (showLogs) console.log("Registru Fiscal:", rows)

    return rows

}

