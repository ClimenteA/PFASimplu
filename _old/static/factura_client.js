

const clientElemIds = ['adresaClient', 'bancaClient',
    'cifClient', 'emailClient', 'ibanClient',
    'nrRegComClient', 'telefonClient']


class ClientForm {

    constructor() {
        this.clienti = []
    }

    oninit(v) {
        m.request({
            method: "GET",
            url: "/clienti"
        }).then(res => {
            this.clienti = res
        })
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


