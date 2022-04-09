import { basePath } from "./config.js"
import { writeCSV } from "https://deno.land/x/csv/mod.ts"


const Months = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie',
    'Mai', 'Iunie', 'Iulie', 'August', 'Septembrie',
    'Octombrie', 'Noiembrie', 'Decembrie']

const range = (min, max) => [...Array(max - min + 1).keys()].map(i => i + min)

function commonItemsList(li1, li2) {
    let filteredArray = li1.filter(value => li2.includes(value))
    return filteredArray
}


function getMonth(date) {
    let parsedDate = new Date(date)
    return Months[parsedDate.getMonth()]
}

function getYear(date) {
    let parsedDate = new Date(date)
    return parsedDate.getFullYear()
}


let plural = {
    "incasare": "incasari",
    "achizitie": "achizitii",
}


function groupRowsByYear(rows) {

    // Group rows by year
    let rowsByYear = {}
    for (let row of rows) {

        let rowDate = new Date(row[0])
        let rowYear = rowDate.getFullYear()

        if (!rowsByYear.hasOwnProperty(rowYear)) {
            rowsByYear[rowYear] = []
        }

        rowsByYear[rowYear].push(row)
    }
    return rowsByYear
}


function getMissingMonths(rowsByYear) {

    let monthsRange = range(0, 12)

    let missingMonths = {}
    for (let [year, rowsYear] of Object.entries(rowsByYear)) {
        for (let month of monthsRange) {
            for (let row of rowsYear) {
                let rmonth = new Date(row[0]).getMonth()
                if (month != rmonth) {

                    if (!missingMonths.hasOwnProperty(year)) {
                        missingMonths[year] = []
                    }

                    if (missingMonths[year].indexOf(month) == -1) {
                        missingMonths[year].push(month)
                    }
                }

            }
        }
    }

    return missingMonths

}


function getEmptyMonths(missingMonths, word) {

    let emptyMonths = []
    for (let [year, months] of Object.entries(missingMonths)) {

        for (let month of months) {

            let monthEmpty = [
                `${year}-${month < 10 ? '0' + String(month) : month}-01`,
                0,
                "0 " + plural[word],
                `Anul ${year} luna ${Months[Number(month)]} nu a inregistrat nici o ${word}`
            ]

            emptyMonths.push(monthEmpty)
        }

    }

    return emptyMonths

}



function fillMonths(rows, word) {

    let rowsByYear = groupRowsByYear(rows)
    let missingMonths = getMissingMonths(rowsByYear)
    let emptyMonths = getEmptyMonths(missingMonths, word)

    let completeRows = [...rows, ...emptyMonths]

    console.log(completeRows)

    return completeRows

}


function fillIncasari(incasarili) {
    return fillMonths(incasarili, "incasare")
}

function fillCheltuieli(cheltuielili) {
    return fillMonths(cheltuielili, "achizitie")
}


function gatherAll(data) {

    // creeaza o lista cu toate incasarile si cheltuielile
    // sorteaza lista in ordine crescatoare dupa data

    let incasarili = fillIncasari(data.incasari.slice(1))
    let cheltuielili = fillCheltuieli(data.cheltuieli.slice(1))

    // console.log("incasarili", incasarili)
    // console.log("cheltuielili", cheltuielili)

    let incasari = []
    for (let li of incasarili) {
        li.push(true) // true incasare
        incasari.push(li)
    }

    let cheltuieli = []
    for (let li of cheltuielili) {
        li.push(false) // false achizitie
        cheltuieli.push(li)
    }

    let allData = [...incasari, ...cheltuieli]

    allData.sort((a, b) => {

        let d1 = new Date(a[0])
        let d2 = new Date(b[0])

        let result = d1 - d2

        return result
    })

    // console.log("Lista incasari cheltuieli sortata dupa data:", allData)

    return allData
}


function getVal(li, tip) {

    // exemplu li 
    // [
    //     "2021-04-20",
    //     123456,
    //     "Factura INV 3",
    //     "../ANAF/An fiscal 2021/Incasari/Factura 2021-04-20 INV 3 123456 RON.pdf",
    //     true
    // ]

    let result = ""
    let incasare = li.at(-1)

    if (tip == "doc") {
        result = li[3]
    }

    if (tip == "fel") {

        if (li[2] == "Factura XX XX") {
            result = '0 incasari'
        } else if (li[2] == '0 achizitii') {
            result = '0 achizitii'
        } else if (li[2].includes('mijlocfix') && li[2].includes('cod') && li[2].includes('amortizat')) {
            result = "Achizitie " + li[2]
        } else {
            if (incasare) result = li[2] != "0 incasari" ? "Incasare " + li[2] : li[2]
            else result = li[2] != "Comision pe operatiune" ? "Achizitie" + " " + li[2] : "Banca " + li[2]
        }

    }

    // Incasari

    if (tip == "incasareNumerar") {

        if (incasare) {
            if (li[2].includes("numerar")) result = li[1]
        }

    }

    if (tip == "incasareBancar") {

        if (incasare) {
            if (li[2].includes("bancar") || incasare) result = li[1]
        }

    }

    // Plati

    if (tip == "plataNumerar") {

        if (!incasare) {
            if (li[2].includes("numerar")) result = li[1]
        }

    }

    if (tip == "plataBancar") {

        if (!incasare) {
            if (li[2].includes("bancar") || !li[2].includes("numerar")) result = li[1]
        }

    }


    return result

}



function getCrtRow(nrCrt, li) {

    let row = [
        nrCrt, // Nr.Crt.
        li[0], // Data
        getVal(li, "doc"), // Documentul (fel, numar)
        getVal(li, "fel"), // Felul operatiunii (explicatii)
        getVal(li, "incasareNumerar") ? getVal(li, "incasareNumerar") : 0, // Incasari Numerar
        getVal(li, "incasareBancar") ? getVal(li, "incasareBancar") : 0, // Incasari Banca
        getVal(li, "plataNumerar") ? getVal(li, "plataNumerar") : 0, // Plati Numerar
        getVal(li, "plataBancar") ? getVal(li, "plataBancar") : 0, // Plati Banca
        // li
    ]

    return row

}


function sumMonthlyRows(idx, rows) {

    let sum = 0
    for (let row of rows) {
        sum = sum + row[idx]
    }
    return sum

}

export async function creeazaRegistruJurnal(data, showLogs) {

    let rows = [
        [
            "Nr.Crt.",
            "Data",
            "Documentul (fel, numar)",
            "Felul operatiunii (explicatii)",
            "Incasari Numerar",
            "Incasari Banca",
            "Plati Numerar",
            "Plati Banca"
        ]
    ]

    let allData = gatherAll(data)

    // console.log("allData", allData)

    let nrCrt = 0
    let monthlyRows = []
    for (let li of allData) {

        nrCrt = nrCrt + 1

        let row = getCrtRow(nrCrt, li)
        rows.push(row)
        monthlyRows.push(row)

        // Calculeaza totalul lunar

        let nextli = allData[allData.indexOf(li) + 1]
        if (nextli == undefined) nextli = "9999-99-99"

        let currMonth = li[0].slice(5, 7)
        let nextMonth = nextli[0].slice(5, 7)

        if (currMonth != nextMonth) {

            if (rows.at(-1)[2] != `Anul ${new Date().getFullYear()} nu a inregistrat nici o achizitie`) {

                // Header
                rows.push([
                    '-',
                    '-',
                    `Calcul total incasari/plati pentru luna ${getMonth(li[0])} (${getYear(li[0])})`,
                    '-',
                    'Total Incasari Numerar',
                    'Total Incasari Bancar',
                    'Total Plati Numerar',
                    'Total Plati Banca'
                ])
                // Calcul 
                rows.push([
                    '-',
                    '-',
                    '-',
                    '-',
                    sumMonthlyRows(4, monthlyRows), // Total Incasari Numerar
                    sumMonthlyRows(5, monthlyRows), // Total Incasari Bancar
                    sumMonthlyRows(6, monthlyRows), // Total Plati Numerar
                    sumMonthlyRows(7, monthlyRows)  // Total Plati Banca
                ])

                monthlyRows = []

            }
        }

    }

    const csvPath = basePath + "/" + "Registru Jurnal.csv"
    const f = await Deno.open(csvPath, { write: true, create: true, truncate: true })
    await writeCSV(f, rows)
    f.close()

    if (showLogs) console.log("Registru Jurnal:", rows)

    return rows

}









