package mijloacefixe

import (
	"encoding/json"
	"io/ioutil"
	"log"
)

type dateIdentificareMijlocFix struct {
	Grupa                 string `json:"grupa"`
	CodClasificare        string `json:"cod_clasificare"`
	DenumireActiveFixe    string `json:"denumire_active_fixe"`
	DurataAmortizareInAni string `json:"durata_amortizare_in_ani"`
}

type CodMijloaceFixe struct {
	Cod dateIdentificareMijlocFix `json:"cod"`
}

func LoadMijloaceFixe() CodMijloaceFixe {

	file, _ := ioutil.ReadFile("./assets/public/coduri_mijloace_fixe_2022.json")

	data := CodMijloaceFixe{}

	err := json.Unmarshal([]byte(file), &data)
	if err != nil {
		log.Panicln(err)
	}

	return data

}
