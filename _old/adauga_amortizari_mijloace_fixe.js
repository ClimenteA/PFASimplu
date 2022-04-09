// ./deno run --allow-all adauga_amortizari_mijloace_fixe.js
import { readJson, getMonthDifference, addMonths } from "./utils.js"



async function rowsMijloaceFixe(path) {
    // "Data", "Cheltuiala", "Descriere", "Path"

    let fmf = readJson(path)

    let amount = parseFloat(fmf.amortizare_lunara.split(" ")[0])
    let description = fmf.fel_serie_numar_data_document
    let extras_path = path

    let luna_darii_in_folosinta = fmf.luna_darii_in_folosinta.length == 2 ? fmf.luna_darii_in_folosinta : "0" + fmf.luna_darii_in_folosinta
    let luna_amortizarii_complete = fmf.luna_amortizarii_complete.length == 2 ? fmf.luna_amortizarii_complete : "0" + fmf.luna_amortizarii_complete
    let ziua_darii_in_folosinta = fmf.anul_darii_in_folosinta + "-" + luna_darii_in_folosinta + "-01"
    let ziua_amortizarii_complete = fmf.anul_amortizarii_complete + "-" + luna_amortizarii_complete + "-01"

    let ziua_darii_in_folosinta_date = new Date(ziua_darii_in_folosinta)
    let ziua_amortizarii_complete_date = new Date(ziua_amortizarii_complete)

    let diff_months = getMonthDifference(ziua_darii_in_folosinta_date, ziua_amortizarii_complete_date)

    let rows = []
    let now = new Date().toISOString().split("T")[0] // 2022-03-29
    for (let i = 1; i <= diff_months; i++) {

        let folosinta_date = new Date(ziua_darii_in_folosinta).toISOString().split("T")[0]
        let added_month = addMonths(folosinta_date, i + 1)

        let date = new Date(added_month).toISOString().split("T")[0]

        rows.push([date, amount, description, extras_path])

        let currDate = new Date(now)
        let iterDate = new Date(date)

        if (iterDate.getFullYear() >= currDate.getFullYear()) {
            if (iterDate.getMonth() >= currDate.getMonth()) {
                break
            }
        }
    }

    return rows

}




export async function adaugaAmortizariMijloaceFixe(mijloacefixe, cheltuieli, showLogs) {

    let toate_cheltuielile = cheltuieli

    for (let an in mijloacefixe) {
        for (let path of mijloacefixe[an]) {

            if (!path.endsWith(".json")) continue

            let rows = await rowsMijloaceFixe(path)

            for (let row of rows) toate_cheltuielile.push(row)
        }
    }

    // if (showLogs) console.log(toate_cheltuielile)

    return toate_cheltuielile

}