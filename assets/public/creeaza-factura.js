function bodyParamString(request, field) {
    if (request[field]) return request[field]
    return ""
}


function round(num) {
    const places = 10 ** 2;
    const res = Math.round(num * places) / places;
    return res
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


// Mithril


const clientElemIds = ['adresaClient',
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
                let partialTotal = parseFloat(document.getElementById("total" + i).value)
                total = total + partialTotal
            }
            document.getElementById("totalFactura").value = round(total)
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
                            "Cantitate",
                            m("input", {
                                onchange: event => {
                                    let sum = parseFloat(document.getElementById("cantitate" + i).value) * parseFloat(document.getElementById("pretPeUnitate" + i).value);
                                    document.getElementById("total" + i).value = round(sum);
                                    calculateTotal();
                                },
                                style: "text-transform:uppercase", step: "any", type: "number", id: "cantitate" + i, name: "cantitate" + i, placeholder: "5"
                            })
                        ]),


                        m("label", { for: "pretPeUnitate" + i }, [
                            "Pret Unitar",
                            m("input", {
                                onchange: event => {
                                    let sum = parseFloat(document.getElementById("cantitate" + i).value) * parseFloat(document.getElementById("pretPeUnitate" + i).value);
                                    document.getElementById("total" + i).value = round(sum);
                                    calculateTotal();
                                },
                                style: "text-transform:uppercase", step: "any", type: "number", id: "pretPeUnitate" + i, name: "pretPeUnitate" + i, placeholder: "4.5"
                            })
                        ]),


                        m("label", { for: "total" + i }, [
                            "Total",
                            m("input", {
                                onfocus: event => {
                                    let sum = parseFloat(document.getElementById("cantitate" + i).value) * parseFloat(document.getElementById("pretPeUnitate" + i).value);
                                    document.getElementById("total" + i).value = round(sum);
                                    calculateTotal();
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
                    "Total de Plata",
                    m("input", { type: "number", step: "any", id: "totalFactura", name: "totalFactura", placeholder: "Ex: 65811429" })
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