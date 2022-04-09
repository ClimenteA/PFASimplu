// import { basePath } from "./config.js"
// import { writeCSV } from "https://deno.land/x/csv/mod.ts"


// "2021-08-12 12.33 RON Transport.jpg" 
// iso date ammount RON description

// "2021-08-10 660.17 RON emag monitor kit tastatura inventar"
// daca inventar este prezent atunci va fi adaugat la inventar
// ce urmeaza dupa inventar va fi considerat obiect de inventar


export async function creeazaFisierulCheltuieli(cheltuieli, showLogs) {

    let rows = [
        [
            "Data",
            "Cheltuiala",
            "Descriere",
            "Path"
        ]
    ]

    for (let an in cheltuieli) {

        if (cheltuieli[an].length == 0) {
            let anulCurent = an.split(' ').at(-1)
            rows.push([anulCurent + '-01-01', 0, '0 achizitii', `Anul ${anulCurent} nu a inregistrat nici o achizitie`])
        }

        for (let path of cheltuieli[an]) {

            let fname = path.split('/').at(-1)
            let fli = fname.split(' ')

            let date = fli[0]
            let amount = parseFloat(fli[1])
            let description = fname.split("RON").at(-1).split(".")[0].trim()

            let row = [date, amount, description, path]

            rows.push(row)

        }
    }

    // const cheltuieli_path = basePath + "/" + "Cheltuieli.csv"
    // const f = await Deno.open(cheltuieli_path, { write: true, create: true, truncate: true })
    // await writeCSV(f, rows)
    // f.close()

    if (showLogs) console.log("Cheltuieli:", rows)

    return rows

}
