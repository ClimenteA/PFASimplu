// ./deno run --allow-all adauga_comisioane_banca.js

import { basePath } from "./config.js"
import { readCSV, readCSVObjects } from "https://deno.land/x/csv/mod.ts"



function parseComision(row, extras_path){

    if (row["tip tranzactie "] == "Comision pe operatiune") {

        let data_procesarii = row["data procesarii"]
        let date = data_procesarii.slice(0,4) + "-" + data_procesarii.slice(4,6) + "-" + data_procesarii.slice(6,8)
        let amount = Math.abs(parseFloat(row.suma))
        let description = "Comision pe operatiune"
        
        return [date, amount, description, extras_path]
    }

    return null
}


async function getCSVRows(extras_path){

    
    let csvRows = []
    
    let f1 = await Deno.open(extras_path)
    for await (const row of readCSVObjects(f1)) {
        // console.log("','", row)
        if (Object.keys(row).length == 1) {
            // console.log("Error ',': ", row)
            f1.close()
            break
        }
        csvRows.push(row)
    }
    
    // Trying another delimitator

    
    if (csvRows.length == 0){
        
        let f2 = await Deno.open(extras_path)

        let options = {
            columnSeparator: ";",
            lineSeparator: "\r\n",
            quote: "$",
        }

        for await (const row of readCSVObjects(f2, options)) {
            // console.log("';'", row)
            if (Object.keys(row).length == 1) {
                // console.log("Error ';': ", row)
                f2.close()
                throw "Nu se poate citi fisierul CSV separatorul trebuie sa fie ',' sau ';'"
            }
    
            csvRows.push(row)
        }

        f2.close()
    }

    // console.log("Linii csv:", csvRows.length, extras_path)

    return csvRows

}


async function rowsComisioane(extras_path){
    // data procesarii : 20211231 -> 2021-08-12
    // suma : -5
    // tip tranzactie : Comision pe operatiune

    let csvRows = await getCSVRows(extras_path)
    let rows = []

    for (let row of csvRows){
        let parsedRow = parseComision(row, extras_path)
        if (parsedRow) rows.push(parsedRow)
    }
   
    return rows

}




export async function adaugaComisioaneBanca(extrase_bancare, cheltuieli, showLogs){

    let toate_cheltuielile = cheltuieli

    for (let an in extrase_bancare) {
        for (let extras_path of extrase_bancare[an]){

            let rows = await rowsComisioane(extras_path)

            for (let row of rows) toate_cheltuielile.push(row)
        }
    }

    // if (showLogs) console.log(toate_cheltuielile)
 
    return toate_cheltuielile
}

