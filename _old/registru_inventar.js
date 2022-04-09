import { basePath } from "./config.js"
import { writeCSV } from "https://deno.land/x/csv/mod.ts"


// https://blog.smartbill.ro/obiecte-de-inventar/
// https://termene.ro/articole/amortizare-active-fixe
// https://www.alegetidrumul.ro/uploads/calificari/177/Materiale%20didactice/IX_Bazele%20contabilitatii_prof_Stanescu%20(10).pdf
// suma_cheltuita / (ani_garantie * 12) => suma amortizata lunar


function getName(li) {

    let name = ""

    if (li[3].includes("inventar")) {
        name = li[3].replace("inventar", "").replace("Achizitie ", "").trim()
    }

    if (li[2].includes("mijlocfix")) {
        name = li[3].split("Achizitie Factura/Bon")[1].trim().split(" ").slice(1,).join(" ")
    }

    return name
}


export async function creeazaRegistruInventar(registruJurnal, showLogs) {

    // exemplu li
    // [
    //     18,
    //     "2021-09-25",
    //     "../ANAF/An fiscal 2021/Cheltuieli/2021-09-25 82.99 RON Flanco Cablu HDMI inventar.jpg",
    //     "Achizitie Flanco Cablu HDMI inventar",
    //     0,
    //     0,
    //     0,
    //     82.99
    // ]
    // Mijloc fix
    // [
    //     32,
    //     "2024-08-31",
    //     "../ANAF/An fiscal 2022/Cheltuieli/FMF 2022-03-09 47000 RON Laptop  mijlocfix 2022-03-27 cod 3_2_4_ a...",
    //     "Achizitie Factura/Bon 2022-03-27 Laptop",
    //     0,
    //     0,
    //     0,
    //     1305.56
    // ]

    let rows = [
        [
            "Nr.Crt.",
            "Denumirea elementelor inventariate",
            "Valoarea de inventar (RON)"
        ]
    ]

    let nrCrt = 0
    let mijloacefixe_adaugate = []
    for (let li of registruJurnal.slice(1)) {

        // Skip calcul total
        if (li[0] == '-') continue

        if (li[2].includes('mijlocfix')) {

            let denumire_suma = li[2] + String(li[7])

            if (!mijloacefixe_adaugate.includes(denumire_suma)) {

                nrCrt = nrCrt + 1

                let denumireObiect = getName(li)
                let valoareInventar = li[2].split("Cheltuieli/FMF")[1].split("RON")[0].trim().split(" ")[1].trim()

                let row = [
                    nrCrt, // Nr.Crt.
                    denumireObiect, // Denumirea elementelor inventariate
                    valoareInventar, // Valoarea de inventar (RON)
                    // li
                ]

                rows.push(row)
                mijloacefixe_adaugate.push(denumire_suma)
            }

        }


        if (li[2].includes('inventar')) {

            nrCrt = nrCrt + 1

            let denumireObiect = getName(li)
            let valoareInventar = li[6] || li[7]

            let row = [
                nrCrt, // Nr.Crt.
                denumireObiect, // Denumirea elementelor inventariate
                valoareInventar, // Valoarea de inventar (RON)
                // li
            ]

            rows.push(row)
        }

    }

    const csvPath = basePath + "/" + "Registru Inventar.csv"
    const f = await Deno.open(csvPath, { write: true, create: true, truncate: true })
    await writeCSV(f, rows)
    f.close()

    if (showLogs) console.log("Registru Inventar:", rows)

    return rows

}

