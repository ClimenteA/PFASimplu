import {
    incasariDB,
    cheltuieliDB,
    clientiDB,
    furnizorDB,
    ultimaIncasareDB
} from "./db.js"


export async function adaugaIncasari(data) {

    let parsedData = {
        facturaPath: data.facturaPath,
        totalFactura: parseFloat(data.totalFactura.split(" ")[0].trim()),
        serie: data.serie,
        numar: parseInt(data.numar),
        data_emitere: data.data_emitere,
        data_scadenta: data.data_scadenta
    }

    await ultimaIncasareDB.remove({})
    await ultimaIncasareDB.insert(parsedData)

    return await incasariDB.insert(parsedData)
}


export async function stergeIncasari(facturaPath) {
    await ultimaIncasareDB.remove({ facturaPath: facturaPath })
    await incasariDB.remove({ facturaPath: facturaPath })
}


export async function getLastInvoice() {
    let results = await ultimaIncasareDB.findOne({})
    return results || {
        serie: 'INV',
        numar: 0
    }
}

export async function getAllClients() {
    return await clientiDB.find({})
}

export async function getFurnizor() {
    let results = await furnizorDB.find({})
    if (results.length > 0) return results.at(-1)
    return {
        nume: null,
        nrRegCom: null,
        cif: null,
        adresa: null,
        telefon: null,
        email: null,
        banca: null,
        iban: null,
    }
}

export async function adaugaCheltuieli(data) {
    return await cheltuieliDB.insert(data)
}

export async function stergeCheltuieli(facturaPath) {
    return await cheltuieliDB.remove({ facturaPath: facturaPath })
}


async function adaugaParti(db, data) {

    let query = { nume: data.nume, email: data.email }
    let parsedData = {
        nume: data.nume,
        nrRegCom: data.nrRegCom,
        cif: data.cif,
        adresa: data.adresa,
        telefon: data.telefon,
        email: data.email,
        banca: data.banca,
        iban: data.iban
    }

    let dataFound = await db.findOne(query)

    if (dataFound) {
        return await db.update(query, { $set: parsedData })
    } else {
        return await db.insert(parsedData)
    }
}


export async function adaugaClient(data) {
    return await adaugaParti(clientiDB, data)
}

export async function adaugaFurnizor(data) {
    return await adaugaParti(furnizorDB, data)
}