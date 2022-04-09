// ./deno run --allow-all web_drash.js
import {
  Drash,
  TengineService,
  existsSync,
  JSZip,
  nanoid
} from "./deps.js"

import { genereazaRapoarte } from "./genereaza_rapoarte.js"
import { XLSX } from "./deps.js"
import { creeaza_factura } from "./factura.js"
import { mijloacefixe } from "./mijloacefixe.js"
import { mijloacefixecod } from "./mijloacefixecod.js"
import { creeaza_mijloc_fix_doc } from "./fisa_mijloc_fix.js"
import { readJson, writeJson } from "./utils.js"
import {
  stergeIncasari,
  adaugaIncasari,
  adaugaClient,
  adaugaFurnizor,
  getLastInvoice,
  getFurnizor,
  getAllClients
} from "./db_operations.js"


// https://docs.google.com/document/d/1Qm2qhXj4IQdCQYAdaG9FFIK1KAGc4pe0/edit#

const tengine = new TengineService({
  views_path: "./templates",
})


class Index extends Drash.Resource {
  paths = ["/"]
  GET(request, response) {
    response.file('./templates/index.html')
  }
}


class PicoCss extends Drash.Resource {
  paths = ["/pico.min.css"]
  GET(request, response) {
    response.file('./static/pico.min.css')
  }
}

class CustomCss extends Drash.Resource {
  paths = ["/custom.css"]
  GET(request, response) {
    response.file('./static/custom.css')
  }
}

class MithrilJs extends Drash.Resource {
  paths = ["/mithril.js"]
  GET(request, response) {
    response.file('./static/mithril.js')
  }
}

class FacturaClientJs extends Drash.Resource {
  paths = ["/factura-client.js"]
  GET(request, response) {
    response.file('./static/factura_client.js')
  }
}



class Success extends Drash.Resource {
  paths = ["/success"]
  GET(request, response) {
    response.file('./templates/success.html')
  }
}


class Failed extends Drash.Resource {
  paths = ["/failed"]
  GET(request, response) {
    response.file('./templates/failed.html')
  }
}



function getPath(data, pathType) {

  let basePath = `../ANAF/An fiscal ${data.split("-")[0]}`

  let paths = {
    "incasari": `${basePath}/Incasari/`,
    "cheltuieli": `${basePath}/Cheltuieli/`,
    "declaratii": `${basePath}/ANAF Declaratii/`
  }

  return paths[pathType]

}




class AdaugaIncasari extends Drash.Resource {
  paths = ["/adauga-incasari"]

  async GET(request, response) {

    const lastInvoice = await getLastInvoice()
    const templateVars = {
      ...lastInvoice
    }
    const html = response.render("/adauga_incasari.html", templateVars)
    response.html(html)

  }

  async POST(request, response) {

    let serie = request.bodyParam("serie")?.toUpperCase()
    let numar = request.bodyParam("numar")
    let data = request.bodyParam("data")
    let suma_incasata = request.bodyParam("suma_incasata")
    let fisier = request.bodyParam("fisier")

    if (fisier.filename.endsWith('.pdf')) {

      fisier.filename = `Factura ${data} ${serie} ${numar} ${suma_incasata} RON.pdf`
      let facturaPath = getPath(data, "incasari") + fisier.filename
      Deno.writeFileSync(facturaPath, fisier.content)

      let date = new Date(data)

      let dateFactura = {
        facturaPath: facturaPath,
        totalFactura: String(suma_incasata) + ' RON',
        serie: serie,
        numar: numar,
        data_emitere: new Date(date).toISOString().split("T")[0],
        data_scadenta: new Date(date.setMonth(date.getMonth() + 1)).toISOString().split("T")[0],
      }

      await adaugaIncasari(dateFactura)

      response.file('./templates/adauga_incasari.html')

    } else {
      response.file('./templates/failed.html')
    }
  }

}




class AdaugaCheltuieli extends Drash.Resource {
  paths = ["/adauga-cheltuieli"]

  GET(request, response) {
    const html = response.render("/adauga_cheltuieli.html", mijloacefixe)
    response.html(html)
  }

  async POST(request, response) {

    let nume_cheltuiala = request.bodyParam("nume_cheltuiala")?.trim()
    let suma_cheltuita = request.bodyParam("suma_cheltuita")
    let tip_tranzactie = request.bodyParam("tip_tranzactie")
    let inventar = request.bodyParam("inventar")
    let data = request.bodyParam("data")
    let fisier = request.bodyParam("fisier")

    let mijlocfix = request.bodyParam("mijlocfix")
    let amortizare_in_ani = request.bodyParam("amortizare_in_ani")
    let data_punerii_in_functiune = request.bodyParam("data_punerii_in_functiune")
    let cod_clasificare = request.bodyParam("cod_clasificare")

    // Exemple nume fisiere
    // 2022-03-03 80 RON Cablu HDMI inventar.jpg
    // 2022-03-17 50000 RON Cheltuieli consumabile bulk.jpg
    // 2022-03-18 100 RON Baterii AA.jpg
    // 2022-03-18 4700 RON Laptop Lenovo mijlocfix 2022-03-18 amortizat 2 ani.jpg
    // 2022-03-15 5555 RON Laptop mijlocfix 2022-03-13 cod 3_2_4_ amortizat 3.jpg

    if (mijlocfix == undefined) {

      fisier.filename = `${data} ${suma_cheltuita} RON ${nume_cheltuiala} ${tip_tranzactie == 'numerar' ? 'numerar' : ''} ${inventar ? "inventar" : ""}.${fisier.filename.split(".").at(-1)}`
      fisier.filename = fisier.filename.replace("  ", " ").replace(" .", ".")
      Deno.writeFileSync(getPath(data, "cheltuieli") + fisier.filename, fisier.content)

    } else {

      fisier.filename = `FMFD ${data} ${suma_cheltuita} RON ${nume_cheltuiala} ${tip_tranzactie == 'numerar' ? 'numerar' : ''} mijlocfix ${data_punerii_in_functiune} cod ${cod_clasificare.split(".").join("_")} amortizat ${amortizare_in_ani}.${fisier.filename.split(".").at(-1)}`
      fisier.filename = fisier.filename.replace("  ", " ").replace(" .", ".")
      let filepath = getPath(data, "cheltuieli") + fisier.filename
      Deno.writeFileSync(filepath, fisier.content)


      // FISA MIJLOC FIX

      // https://blog.smartbill.ro/obiecte-de-inventar/
      // https://www.agentiabrasov.ro/wp-content/uploads/2018/11/anexa-8-model-fisa-mijlocului-fix-.pdf

      let folosintaDate = new Date(data_punerii_in_functiune)
      let incepereAmortizareDate = new Date(folosintaDate.setMonth(folosintaDate.getMonth() + 1))
      let amortizareDate = new Date(incepereAmortizareDate.setFullYear(
        incepereAmortizareDate.getFullYear() + parseInt(amortizare_in_ani)
      ))
      let amortizare_lunara = (parseFloat(suma_cheltuita) / (parseInt(amortizare_in_ani) * 12)).toFixed(2)
      let cota_de_amortizare = (parseFloat(amortizare_lunara) / parseFloat(suma_cheltuita) * 100).toFixed(2)

      let zip_path = getPath(data, "cheltuieli") + nanoid() + ".zip"

      let fisa_mijloc_fix = {
        // col1
        nr_inventar: "0",
        fel_serie_numar_data_document: "Factura/Bon " + data_punerii_in_functiune + " " + nume_cheltuiala, // 47
        valoare_inventar: String(suma_cheltuita) + " RON", //"5555 RON"
        amortizare_lunara: String(amortizare_lunara) + " RON", // "154.31 RON"
        denumire_si_caracteristici: "Specificate in factura/bon",
        accesorii: "Specificate in factura/bon",
        // col2
        grupa: String(mijloacefixecod[cod_clasificare].grupa).slice(0, 20) + "...", // 3
        cod_clasificare: String(mijloacefixecod[cod_clasificare].cod_clasificare), // "3.2.4."
        anul_darii_in_folosinta: String(folosintaDate.getFullYear()), // "2022"
        luna_darii_in_folosinta: String(folosintaDate.getMonth()), // "3"
        anul_amortizarii_complete: String(amortizareDate.getFullYear()), // "2025"
        luna_amortizarii_complete: String(amortizareDate.getMonth()), //"3"
        durata_normala_de_functionare: String(mijloacefixecod[cod_clasificare].durata_amortizare_in_ani), // "3-5 ani",
        cota_de_amortizare: String(cota_de_amortizare), // 2.75
        cale_document_justificativ: filepath,
        zip_path: zip_path
      }

      let path_fisa = getPath(data, "cheltuieli")

      let nume_fisa_mijloc_fix = `FMF ${data} ${suma_cheltuita} RON ${nume_cheltuiala} ${tip_tranzactie == 'numerar' ? 'numerar' : ''} mijlocfix ${data_punerii_in_functiune} cod ${cod_clasificare.split(".").join("_")} amortizat ${amortizare_in_ani}`

      let nume_fisa_mijloc_fix_json = nume_fisa_mijloc_fix + ".json"
      let nume_fisa_mijloc_fix_pdf = nume_fisa_mijloc_fix + ".pdf"

      let fisa_mijloc_fix_path = path_fisa + nume_fisa_mijloc_fix_pdf
      let fisa_mijloc_fix_json_path = path_fisa + nume_fisa_mijloc_fix_json

      writeJson(fisa_mijloc_fix_json_path, fisa_mijloc_fix)
      await creeaza_mijloc_fix_doc(fisa_mijloc_fix, fisa_mijloc_fix_path)

      const zip = new JSZip()

      const filepath_zip = await Deno.open(filepath, { read: true })
      const filepath_bytes = await Deno.readAll(filepath_zip)
      zip.addFile(fisier.filename, filepath_bytes)

      const fisa_mijloc_fix_json_path_zip = await Deno.open(fisa_mijloc_fix_json_path, { read: true })
      const fisa_mijloc_fix_json_path_zip_bytes = await Deno.readAll(fisa_mijloc_fix_json_path_zip)
      zip.addFile(nume_fisa_mijloc_fix_json, fisa_mijloc_fix_json_path_zip_bytes)

      const fisa_mijloc_fix_path_zip = await Deno.open(fisa_mijloc_fix_path, { read: true })
      const fisa_mijloc_fix_path_bytes = await Deno.readAll(fisa_mijloc_fix_path_zip)
      zip.addFile(nume_fisa_mijloc_fix_pdf, fisa_mijloc_fix_path_bytes)

      await zip.writeZip(zip_path)

    }

    this.redirect("/adauga-cheltuieli", response)
  }
}


class AdaugaDeclaratii extends Drash.Resource {
  paths = ["/adauga-declaratii"]

  GET(request, response) {
    response.file('./templates/adauga_declaratii.html')
  }

  POST(request, response) {

    let data = request.bodyParam("data")
    let fisier = request.bodyParam("fisier")

    Deno.writeFileSync(getPath(data, "declaratii") + fisier.filename, fisier.content)

    response.file('./templates/success.html')

  }
}


class RegistreContabile extends Drash.Resource {
  paths = ["/registre-contabile"]

  async GET(request, response) {
    let registre = await genereazaRapoarte()
    const html = response.render("/registre_contabile.html", registre)
    response.html(html)
  }
}


class DownloadFisier extends Drash.Resource {

  paths = ["/download-fisier"]

  async POST(request, response) {

    let filePath = request.bodyParam("filePath")

    if (filePath.includes("mijlocfix")) {

      let data = readJson(filePath)
      response.download(data.zip_path, "application/octedstream")

    } else {
      response.download(filePath, "application/octedstream")
    }

  }
}


class StergeFisier extends Drash.Resource {

  paths = ["/sterge-fisier"]

  async POST(request, response) {

    let filePath = request.bodyParam("filePath")

    if (filePath.includes("Incasari")) {
      await stergeIncasari(filePath)
    }

    if (filePath.includes("mijlocfix")) {

      let data = readJson(filePath)
      // Delete bon/factura file
      if (existsSync(data.cale_document_justificativ)) {
        Deno.removeSync(data.cale_document_justificativ)
      }
      if (existsSync(data.zip_path)) {
        Deno.removeSync(data.zip_path)
      }

      // Delete json file
      let jsonFile = filePath
      if (existsSync(jsonFile)) {
        Deno.removeSync(jsonFile)
      }

      // Delete pdf mijlocfix file
      let mijlocfixpdf = filePath.replace(".json", ".pdf")
      if (existsSync(mijlocfixpdf)) {
        Deno.removeSync(mijlocfixpdf)
      }


    } else {

      Deno.removeSync(filePath)

    }

    this.redirect("/registre-contabile", response)

  }

}



const registre = {
  "jurnal": "../ANAF/Registru Jurnal.csv",
  "inventar": "../ANAF/Registru Inventar.csv",
  "fiscal": "../ANAF/Registru Fiscal.csv"

}

class DownloadRegistreCSV extends Drash.Resource {
  paths = ["/download-registru-csv/:registru"]

  GET(request, response) {
    let nume = request.pathParam("registru")
    response.download(registre[nume], "application/CSV")
  }
}


class DownloadRegistreXLSX extends Drash.Resource {
  paths = ["/download-registru-xlsx/:registru"]

  async GET(request, response) {

    let csvPath = registre[request.pathParam("registru")]
    let xlPath = csvPath.replace(".csv", ".xlsx")

    let workbook = XLSX.readFile(csvPath, { raw: true })
    XLSX.writeFile(workbook, xlPath)

    response.download(xlPath, "application/octet-stream")
  }
}


function bodyParamString(request, param) {
  return request.bodyParam(param) ? String(request.bodyParam(param)) : ""
}



class DelFacturaService extends Drash.Service {
  runAfterResource(request, response) {

    let jsonPath = "./static/deleteInvoice.json"

    if (existsSync(jsonPath)) {
      let data = readJson(jsonPath)
      Deno.removeSync(data.invoicePath)
      Deno.removeSync(jsonPath)
    }
  }
}


class GetClients extends Drash.Resource {
  paths = ["/clienti"]
  async GET(request, response) {
    const clients = await getAllClients()
    response.json(clients)
  }
}


class CreeazaFactura extends Drash.Resource {
  paths = ["/creeaza-factura"]

  services = {
    POST: [new DelFacturaService()]
  }

  async GET(request, response) {

    const lastInvoice = await getLastInvoice()
    const furnizor = await getFurnizor()

    const templateVars = {
      ...lastInvoice,
      ...furnizor
    }

    const html = response.render("/creeaza_factura.html", templateVars)
    response.html(html)
  }

  async POST(request, response) {

    let dateFactura = {
      'totalFactura': bodyParamString(request, "totalFactura") + ' RON',
      'serie': bodyParamString(request, "serie").toUpperCase(),
      'numar': bodyParamString(request, "numar").padStart(6, '0'),
      'data': bodyParamString(request, "data"),
      'adauga_la_incasari': bodyParamString(request, "adauga_la_incasari")
    }

    // '../ANAF/Factura 2022-03-21 FAB22 12 1000000 RON.pdf'
    let numeFactura = `Factura ${dateFactura.data} ${dateFactura.serie} ${String(parseInt(dateFactura.numar))} ${dateFactura.totalFactura}.pdf`
    dateFactura['facturaPath'] = `../ANAF/An fiscal ${dateFactura.data.split('-')[0]}/Incasari/${numeFactura}`

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

    let pdfPath = await creeaza_factura(dateFactura)

    if (dateFactura.adauga_la_incasari == undefined) {
      writeJson("./static/deleteInvoice.json", { invoicePath: pdfPath })
    } else {

      await adaugaIncasari(dateFactura)
      await adaugaClient(dateFactura.client)
      await adaugaFurnizor(dateFactura.furnizor)

    }

    response.download(pdfPath, "application/pdf")

  }

}





const server = new Drash.Server({
  hostname: "localhost",
  port: 3000,
  protocol: "http",
  services: [tengine],
  resources: [
    Index,
    PicoCss,
    CustomCss,
    Success,
    Failed,
    AdaugaIncasari,
    AdaugaCheltuieli,
    AdaugaDeclaratii,
    RegistreContabile,
    DownloadRegistreCSV,
    DownloadRegistreXLSX,
    StergeFisier,
    DownloadFisier,
    CreeazaFactura,
    MithrilJs,
    FacturaClientJs,
    GetClients,
  ],
})

server.run()
console.log(`\nDeschide browserul la adresa: ${server.address}. (click pe link)\n`)