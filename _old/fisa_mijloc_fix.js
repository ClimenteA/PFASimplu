// ./deno run --allow-all completare_fisa_mijloc_fix.js

import { PDFDocument, StandardFonts, rgb } from "./libs/pdf-lib.esm.js"



// https://www.alegetidrumul.ro/uploads/calificari/177/Materiale%20didactice/IX_Bazele%20contabilitatii_prof_Stanescu%20(10).pdf



export async function creeaza_mijloc_fix_doc(fisa_mijloc_fix, fisa_mijloc_fix_path) {

    const file = await Deno.open("./static/model_fisa_mijloc_fix.pdf", { read: true })
    const model_fisa_mijloc_fix = await Deno.readAll(file)

    const pdfDoc = await PDFDocument.load(model_fisa_mijloc_fix)
    pdfDoc.setTitle('MIJLOC FIX')
    const pages = pdfDoc.getPages()

    const { width, height } = pages[0].getSize() // 595.28 841.89


    // Nr. Inventar:
    pages[0].moveTo(135, 661)
    pages[0].drawText(fisa_mijloc_fix.nr_inventar, { size: 10 })

    // Fel, serie, nr. data document provenienţă:
    pages[0].moveTo(70, 625)
    pages[0].drawText(fisa_mijloc_fix.fel_serie_numar_data_document, { size: 10 })

    // Valoare de inventar:
    pages[0].moveTo(70, 589)
    pages[0].drawText(fisa_mijloc_fix.valoare_inventar, { size: 10 })

    // Amortizare lunară:
    pages[0].moveTo(70, 552)
    pages[0].drawText(fisa_mijloc_fix.amortizare_lunara, { size: 10 })


    // Denumirea mijlocului fix şi caracteristici tehnice
    pages[0].moveTo(70, 516)
    pages[0].drawText(fisa_mijloc_fix.denumire_si_caracteristici, { size: 10 })

    // Accesorii:
    pages[0].moveTo(70, 418)
    pages[0].drawText(fisa_mijloc_fix.accesorii, { size: 10 })


    pages[0].moveTo(350, 695)
    pages[0].drawText(fisa_mijloc_fix.grupa, { size: 10 })

    pages[0].moveTo(410, 658)
    pages[0].drawText(fisa_mijloc_fix.cod_clasificare, { size: 10 })

    pages[0].moveTo(350, 600)
    pages[0].drawText(fisa_mijloc_fix.anul_darii_in_folosinta, { size: 10 })

    pages[0].moveTo(350, 576)
    pages[0].drawText(fisa_mijloc_fix.luna_darii_in_folosinta, { size: 10 })

    pages[0].moveTo(350, 516)
    pages[0].drawText(fisa_mijloc_fix.anul_amortizarii_complete, { size: 10 })

    pages[0].moveTo(350, 490)
    pages[0].drawText(fisa_mijloc_fix.luna_amortizarii_complete, { size: 10 })

    pages[0].moveTo(350, 430)
    pages[0].drawText(fisa_mijloc_fix.durata_normala_de_functionare, { size: 10 })

    pages[0].moveTo(404, 394)
    pages[0].drawText(fisa_mijloc_fix.cota_de_amortizare, { size: 10 })


    const pdfBytes = await pdfDoc.save()

    await Deno.writeFile(fisa_mijloc_fix_path, pdfBytes)

    return fisa_mijloc_fix_path

}

