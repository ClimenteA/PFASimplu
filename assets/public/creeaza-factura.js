
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


function bodyParamString(request, field) {
    if (request[field]) return request[field]
    return ""
}

function proceseazaRawData(request) {

    let dateFactura = {
        'totalFactura': bodyParamString(request, "totalFactura") + ' RON',
        'serie': bodyParamString(request, "serie").toUpperCase(),
        'numar': bodyParamString(request, "numar").padStart(6, '0'),
        'data': bodyParamString(request, "data"),
        'adauga_la_incasari': bodyParamString(request, "adauga_la_incasari")
    }

    // '../ANAF/Factura 2022-03-21 FAB22 12 1000000 RON.pdf'
    // let numeFactura = `Factura ${dateFactura.data} ${dateFactura.serie} ${String(parseInt(dateFactura.numar))} ${dateFactura.totalFactura}.pdf`
    // dateFactura['facturaPath'] = `../ANAF/An fiscal ${dateFactura.data.split('-')[0]}/Incasari/${numeFactura}`

    dateFactura['furnizor'] = {
        nume: bodyParamString(request, "numeFurnizor").toUpperCase(),
        nrRegCom: bodyParamString(request, "nrRegComFurnizor").toUpperCase(),
        cif: bodyParamString(request, "cifFurnizor"),
        adresa: bodyParamString(request, "adresaFurnizor").toUpperCase(),
        telefon: bodyParamString(request, "telefonFurnizor"),
        email: bodyParamString(request, "emailFurnizor").toLowerCase(),
        banca: bodyParamString(request, "bancaFurnizor").toUpperCase(),
        iban: bodyParamString(request, "ibanFurnizor").toUpperCase()
    }

    dateFactura['client'] = {
        nume: bodyParamString(request, "numeClient").toUpperCase(),
        nrRegCom: bodyParamString(request, "nrRegComClient").toUpperCase(),
        cif: bodyParamString(request, "cifClient"),
        adresa: bodyParamString(request, "adresaClient").toUpperCase(),
        telefon: bodyParamString(request, "telefonClient"),
        email: bodyParamString(request, "emailClient").toLowerCase(),
        banca: bodyParamString(request, "bancaClient").toUpperCase(),
        iban: bodyParamString(request, "ibanClient").toUpperCase()
    }


    let produseServicii = []

    for (let i = 0; i < 20; i++) {

        produseServicii.push({

            'denumire': bodyParamString(request, 'denumire' + i).toUpperCase(),
            'unitateDeMasura': bodyParamString(request, 'unitateDeMasura' + i).toUpperCase(),
            'cantitate': bodyParamString(request, 'cantitate' + i).toUpperCase(),
            'pretPeUnitate': bodyParamString(request, 'pretPeUnitate' + i).toUpperCase(),
            'total': bodyParamString(request, 'total' + i)

        })

    }

    dateFactura['produseServicii'] = produseServicii

    let date = new Date(dateFactura.data)

    dateFactura['data_emitere'] = dateFactura.data
    dateFactura['data_scadenta'] = new Date(date.setMonth(date.getMonth() + 1)).toISOString().split("T")[0]
    dateFactura['nota'] = dateFactura.nota ? "Nota: " + dateFactura.nota : ""

    return dateFactura

}


async function creeaza_factura(RawDateFactura) {

    let dateFactura = proceseazaRawData(RawDateFactura)

    const url = 'http://localhost:3000/model_factura.pdf'
    const model_factura_bytes = await fetch(url).then(res => res.arrayBuffer())

    const pdfDoc = await PDFLib.PDFDocument.load(model_factura_bytes)
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

    return {
        bytes: pdfBytes,
        data: dateFactura
    }

}





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







// Mithril


const clientElemIds = ['adresaClient', 'bancaClient',
    'cifClient', 'emailClient', 'ibanClient',
    'nrRegComClient', 'telefonClient']


class ClientForm {

    constructor() {
        this.clienti = []
    }

    getClients() {

        m.request({
            method: "GET",
            url: "/clienti"
        }).then(res => {
            console.log("CLIENTI:", res)
            this.clienti = res
        });
    }

    getFurnizor() {

        m.request({
            method: "GET",
            url: "/furnizor"
        }).then(furnizorObj => {

            console.log("FURNIZOR: ", furnizorObj)

            for (let key in furnizorObj) {
                let elementId = key;

                if (key == "serie") {
                    elementId = key;
                } else if (key == "numar") {
                    elementId = key;
                } else {
                    elementId = key + "Furnizor";
                }

                let el = document.getElementById(elementId);
                if (!el) continue;

                if (key == "numar") {
                    el.value = parseInt(furnizorObj[key]) + 1;
                } else {
                    el.value = furnizorObj[key];
                }

            }
        });

    }

    oninit(v) {

        this.getClients();
        this.getFurnizor();

    }

    fillClientData(event) {

        let selectedClient = null
        for (let i = 0; i < this.clienti.length; i++) {
            if (event.target.value == this.clienti[i].nume) {
                selectedClient = this.clienti[i]
                break
            }
        }

        if (selectedClient) {

            for (const key in selectedClient) {
                let elementId = key + "Client";
                let el = document.getElementById(elementId);
                if (!el) continue;
                el.value = selectedClient[key];
            }

        } else {

            for (const elementId of clientElemIds) {
                let el = document.getElementById(elementId);
                if (!el) continue;
                el.value = null;
            }

        }
    }

    view(v) {

        return [
            m('label', { 'for': 'numeClient' }, [
                m('span', 'Nume'),
                m('input', {
                    list: "clienti",
                    style: "text-transform:uppercase",
                    type: "text",
                    id: "numeClient",
                    name: "numeClient",
                    placeholder: "Dan Rogu",
                    required: true,
                    onchange: event => this.fillClientData(event)
                }),
                m("datalist", { id: "clienti" }, this.clienti.map(c => {
                    return m('option', { value: c.nume })
                }))
            ])
        ]
    }
}





class DateComp {

    getCurrentDate() {
        return new Date().toISOString().split('T')[0]
    }

    view(v) {

        return [
            m('label', { "for": "data" }, [
                m('span', "Data factura"),
                m("input", { "type": "date", "id": "data", "name": "data", "required": true, "value": this.getCurrentDate() })
            ])
        ]
    }
}

class Billable {


    view(v) {

        function calculateTotal() {
            let total = 0
            for (let i = 0; i < v.attrs.billables.length; i++) {
                let partialTotal = Number(document.getElementById("total" + i).value)
                total = total + partialTotal
            }
            document.getElementById("totalFactura").value = total
        }


        return [

            v.attrs.billables.map(i => {
                return m("div", { id: 'livrabil' + i, style: "border: 2px solid lightgray;padding:1rem;margin-top:1rem;border-radius:var(--border-radius)" }, [

                    m("label", { for: "denumire" + i }, [
                        "Denumire produse sau servicii",
                        m("input", { style: "text-transform:uppercase", type: "text", id: "denumire" + i, name: "denumire" + i, placeholder: "Servicii IT" })
                    ]),

                    m('.grid', [

                        m("label", { for: "unitateDeMasura" + i }, [
                            "U.M.",
                            m("input", { style: "text-transform:uppercase", type: "text", id: "unitateDeMasura" + i, name: "unitateDeMasura" + i, placeholder: "ore" })
                        ]),

                        m("label", { for: "cantitate" + i }, [
                            "Cant.",
                            m("input", {
                                onchange: event => {
                                    let sum = Number(document.getElementById("cantitate" + i).value) * Number(document.getElementById("pretPeUnitate" + i).value)
                                    document.getElementById("total" + i).value = sum
                                    calculateTotal()
                                },
                                style: "text-transform:uppercase", step: "any", type: "number", id: "cantitate" + i, name: "cantitate" + i, placeholder: "5"
                            })
                        ]),


                        m("label", { for: "pretPeUnitate" + i }, [
                            "Pret",
                            m("input", {
                                onchange: event => {
                                    let sum = Number(document.getElementById("cantitate" + i).value) * Number(document.getElementById("pretPeUnitate" + i).value)
                                    document.getElementById("total" + i).value = sum
                                    calculateTotal()
                                },
                                style: "text-transform:uppercase", step: "any", type: "number", id: "pretPeUnitate" + i, name: "pretPeUnitate" + i, placeholder: "4.5"
                            })
                        ]),


                        m("label", { for: "total" + i }, [
                            "Total (RON)",
                            m("input", {
                                onfocus: event => {
                                    let sum = Number(document.getElementById("cantitate" + i).value) * Number(document.getElementById("pretPeUnitate" + i).value)
                                    document.getElementById("total" + i).value = sum
                                    calculateTotal()
                                },
                                style: "text-transform:uppercase", step: "any", type: "number", id: "total" + i, name: "total" + i, placeholder: "22.5"
                            })
                        ]),

                    ])
                ])
            }),


            m("#totalDePlataDiv", {
                style: v.attrs.billables.length > 0 ? "border: 2px solid lightgray;padding:1rem;margin-top:3rem;border-radius:var(--border-radius)" : "display:none;"
            }, [
                m("label", { for: "totalFactura" }, [
                    "Total de Plata (RON)",
                    m("input", { type: "number", id: "totalFactura", name: "totalFactura", placeholder: "Ex: 65811429" })
                ])
            ])
        ]
    }

}


class BillablesApp {

    constructor() {
        this.state = { billables: [], counter: 0 }
    }

    addBillable(event) {
        event.preventDefault()

        if (this.state.counter < 16) {
            this.state.billables.push(this.state.counter)
            this.state.counter++
        }

    }

    removeBillable(event) {
        event.preventDefault()

        if (this.state.counter > 0) {
            this.state.billables.pop()
            this.state.counter--
        }

    }

    view(v) {
        return [

            m('.grid', [

                m('button', {
                    onclick: event => this.addBillable(event),
                    style: "background-color:lightseagreen;margin-top:0.5rem;"
                }, "ADAUGA LIVRABIL"),

                m('button', {
                    onclick: event => this.removeBillable(event),
                    style: "background-color:lightcoral;margin-top:0.5rem;"
                }, "SCOATE LIVRABIL"),
            ]),

            m(Billable, { billables: this.state.billables }),

        ]
    }
}


function mountComponents() {

    m.mount(
        document.getElementById("billables"),
        BillablesApp
    );

    m.mount(
        document.getElementById("data_container"),
        DateComp
    );


    m.mount(
        document.getElementById("numeClientContainer"),
        ClientForm
    );



}