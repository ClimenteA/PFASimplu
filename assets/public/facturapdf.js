
// import { PDFDocument } from "/pdf-lib.esm.js"


const splitAt = (index, xs) => [xs.slice(0, index), xs.slice(index)]


function getSafeAddress(adresa) {

    let adresaSafe = adresa

    if (adresa.length > 39) {
        let half = parseInt(adresa.length / 2)
        let adresaUnderscore = adresa.split(" ").join("_")
        let breakIndex = half
        for (let i = half; i < adresaUnderscore.length; i++) {
            if (adresaUnderscore.charAt(i) != "_") {
                breakIndex = i
                adresaSafe = splitAt(breakIndex, adresaSafe).join('\n')
                break
            }
        }
    }

    return adresaSafe

}



async function creeaza_factura(event) {


    let dateFactura = {}

    const file = await Deno.open("./static/model_factura.pdf", { read: true })
    const model_factura_bytes = await Deno.readAll(file)

    const pdfDoc = await PDFDocument.load(model_factura_bytes)
    pdfDoc.setTitle(`FACTURA ${dateFactura.serie} ${dateFactura.numar} ${dateFactura.data_emitere}`)

    const pages = pdfDoc.getPages()

    const { width, height } = pages[0].getSize() // 595.28 841.89

    dateFactura.furnizor.adresa = getSafeAddress(dateFactura.furnizor.adresa)
    dateFactura.client.adresa = getSafeAddress(dateFactura.client.adresa)

    // Serie
    pages[0].moveTo(345, 753)
    pages[0].drawText(dateFactura.serie, { size: 10 })

    // Numar
    pages[0].moveTo(353, 741)
    pages[0].drawText(dateFactura.numar, { size: 10 })

    // Data emitere
    pages[0].moveTo(505, 753)
    pages[0].drawText(dateFactura.data_emitere, { size: 10 })

    // Data scadenta
    pages[0].moveTo(513, 741)
    pages[0].drawText(dateFactura.data_scadenta, { size: 10 })


    // Furnizor
    pages[0].moveTo(130, 642)
    pages[0].drawText(dateFactura.furnizor.nume, { size: 14 })

    pages[0].moveTo(130, 620)
    pages[0].drawText(dateFactura.furnizor.nrRegCom, { size: 10 })

    pages[0].moveTo(130, 602)
    pages[0].drawText(dateFactura.furnizor.cif, { size: 10 })

    pages[0].moveTo(130, 582)
    pages[0].drawText(dateFactura.furnizor.adresa, { size: 10, lineHeight: 12 })

    pages[0].moveTo(130, 550)
    pages[0].drawText(dateFactura.furnizor.telefon, { size: 10 })

    pages[0].moveTo(130, 533)
    pages[0].drawText(dateFactura.furnizor.email, { size: 10 })

    pages[0].moveTo(130, 513)
    pages[0].drawText(dateFactura.furnizor.banca, { size: 10 })

    pages[0].moveTo(130, 495)
    pages[0].drawText(dateFactura.furnizor.iban, { size: 10 })


    // Client
    pages[0].moveTo(342, 642)
    pages[0].drawText(dateFactura.client.nume, { size: 14 })

    pages[0].moveTo(342, 620)
    pages[0].drawText(dateFactura.client.nrRegCom, { size: 10 })

    pages[0].moveTo(342, 602)
    pages[0].drawText(dateFactura.client.cif, { size: 10 })

    pages[0].moveTo(342, 582)
    pages[0].drawText(dateFactura.client.adresa, { size: 10, lineHeight: 12 })

    pages[0].moveTo(342, 550)
    pages[0].drawText(dateFactura.client.telefon, { size: 10 })

    pages[0].moveTo(342, 533)
    pages[0].drawText(dateFactura.client.email, { size: 10 })

    pages[0].moveTo(342, 513)
    pages[0].drawText(dateFactura.client.banca, { size: 10 })

    pages[0].moveTo(342, 495)
    pages[0].drawText(dateFactura.client.iban, { size: 10 })


    // TOTAL DE PLATA

    pages[0].moveTo(400, 435)
    pages[0].drawText(dateFactura.totalFactura, { size: 14 })


    // PRODUSE/SERVICII

    // 1 Row
    pages[0].moveTo(53, 368)
    pages[0].drawText(dateFactura.produseServicii[0].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[0].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[0].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[0].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[0].total, { size: 10 })


    // 2 Row
    pages[0].moveTo(53, 349)
    pages[0].drawText(dateFactura.produseServicii[1].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[1].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[1].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[1].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[1].total, { size: 10 })


    // 3 Row
    pages[0].moveTo(53, 329)
    pages[0].drawText(dateFactura.produseServicii[2].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[2].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[2].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[2].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[2].total, { size: 10 })


    // 4 Row
    pages[0].moveTo(53, 310)
    pages[0].drawText(dateFactura.produseServicii[3].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[3].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[3].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[3].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[3].total, { size: 10 })


    // 5 Row
    pages[0].moveTo(53, 292)
    pages[0].drawText(dateFactura.produseServicii[4].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[4].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[4].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[4].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[4].total, { size: 10 })


    // 6 Row
    pages[0].moveTo(53, 275)
    pages[0].drawText(dateFactura.produseServicii[5].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[5].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[5].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[5].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[5].total, { size: 10 })


    // 7 Row
    pages[0].moveTo(53, 256)
    pages[0].drawText(dateFactura.produseServicii[6].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[6].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[6].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[6].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[6].total, { size: 10 })


    // 8 Row
    pages[0].moveTo(53, 238)
    pages[0].drawText(dateFactura.produseServicii[7].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[7].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[7].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[7].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[7].total, { size: 10 })

    // 9 Row
    pages[0].moveTo(53, 222)
    pages[0].drawText(dateFactura.produseServicii[8].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[8].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[8].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[8].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[8].total, { size: 10 })


    // 10 Row
    pages[0].moveTo(53, 203)
    pages[0].drawText(dateFactura.produseServicii[9].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[9].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[9].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[9].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[9].total, { size: 10 })


    // 11 Row
    pages[0].moveTo(53, 185)
    pages[0].drawText(dateFactura.produseServicii[10].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[10].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[10].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[10].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[10].total, { size: 10 })


    // 12 Row
    pages[0].moveTo(53, 168)
    pages[0].drawText(dateFactura.produseServicii[11].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[11].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[11].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[11].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[11].total, { size: 10 })

    // 13 Row
    pages[0].moveTo(53, 148)
    pages[0].drawText(dateFactura.produseServicii[12].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[12].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[12].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[12].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[12].total, { size: 10 })

    // 14 Row
    pages[0].moveTo(53, 130)
    pages[0].drawText(dateFactura.produseServicii[13].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[13].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[13].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[13].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[13].total, { size: 10 })


    // 15 Row
    pages[0].moveTo(53, 112)
    pages[0].drawText(dateFactura.produseServicii[14].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[14].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[14].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[14].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[14].total, { size: 10 })

    // 16 Row
    pages[0].moveTo(53, 96)
    pages[0].drawText(dateFactura.produseServicii[14].denumire, { size: 10 })

    pages[0].moveRight(290)
    pages[0].drawText(dateFactura.produseServicii[14].unitateDeMasura, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[14].cantitate, { size: 10 })

    pages[0].moveRight(62)
    pages[0].drawText(dateFactura.produseServicii[14].pretPeUnitate, { size: 10 })

    pages[0].moveRight(50)
    pages[0].drawText(dateFactura.produseServicii[14].total, { size: 10 })


    // Nota
    pages[0].moveTo(50, 60)
    pages[0].drawText(dateFactura.nota, { size: 10 })


    const pdfBytes = await pdfDoc.save()

    return pdfBytes

}



document.getElementById("creeaza-factura").addEventListener("onsubmit", creeaza_factura, false);



let exampluDateFactura = {
    'facturaPath': '../ANAF/Factura 2022-03-21 FAB22 001230 1000000 RON.pdf',
    'totalFactura': '1.000.000 RON',
    'serie': 'FAB22',
    'numar': '001230',
    'data_emitere': '21-03-2022',
    'data_scadenta': '21-04-2022',
    'nota': 'Nota: factura este valabila fara stampila',
    'furnizor': {
        'nume': "Jean Paul Constanza PFA",
        'nrRegCom': 'JXX/XXXX/XXXX',
        'cif': '11111111',
        'adresa': 'IASI, SOS.NATIONALA, NR.111 BL.A1, SC.A, AP.1 wsdsdsdsdsddsds ds d s sd sdsd3   sd',
        'telefon': '(+40)0724111111',
        'email': 'jeanpaulconstanzapfa@gmail.com',
        'banca': 'ING',
        'iban': 'RO01INGB0011111111111111'
    },
    'client': {
        'nume': "Alexandru Pinterest",
        'nrRegCom': 'FXX/XXXX/XXXX',
        'cif': '11111111',
        'adresa': 'SOS. REGIONALA, NR.1 MUN. BRASOV',
        'telefon': '(+40)0724111111',
        'email': 'alexandrupinteresst@gmail.com',
        'banca': 'ING',
        'iban': 'RO01INGB0011111111111111'
    },
    'produseServicii': [
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        },
        {
            'denumire': "Servicii IT",
            'unitateDeMasura': 'ore',
            'cantitate': '134',
            'pretPeUnitate': '1.4',
            'total': '135.4'
        }
    ]
}


// await creeaza_factura(exampluDateFactura)