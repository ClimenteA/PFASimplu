// import { basePath } from "./config.js"
// import { writeCSV } from "https://deno.land/x/csv/mod.ts"


// "Factura 2021-02-18 INV 1 1111 RON.pdf"
// Factura YYYY-MM-DD seria nr suma RON


export async function creeazaFisierulIncasari(incasari, showLogs) {

    let rows = [
        [
            "Data",
            "Incasare",
            "Descriere",
            "Path"
        ]
    ]

    for (let an in incasari) {

        if (incasari[an].length == 0) {
            let anulCurent = an.split(' ').at(-1)
            rows.push([anulCurent + '-01-01', 0, '0 incasari', `Anul ${anulCurent} nu a inregistrat nici o incasare`])
        }

        for (let path of incasari[an]) {

            let fname = path.split('/').at(-1)
            let fli = fname.split(' ')

            let date = fli[1]
            let amount = parseFloat(fli[4])
            let description = fli[0] + ' ' + fli[2] + ' ' + fli[3]

            let row = [date, amount, description, path]

            rows.push(row)

        }
    }

    // const incasari_path = basePath + "/" + "Incasari.csv"
    // const f = await Deno.open(incasari_path, { write: true, create: true, truncate: true })
    // await writeCSV(f, rows)
    // f.close()

    if (showLogs) console.log("Incasari:", rows)

    return rows

}
