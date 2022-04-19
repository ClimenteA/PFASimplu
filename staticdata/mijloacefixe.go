package staticdata

import (
	"encoding/json"
	"io/ioutil"
	"log"
)

type CodMijloaceFixe struct {
	Grupa                 string `json:"grupa"`
	CodClasificare        string `json:"cod_clasificare"`
	DenumireActiveFixe    string `json:"denumire_active_fixe"`
	DurataAmortizareInAni string `json:"durata_amortizare_in_ani"`
}

func LoadMijloaceFixe() []CodMijloaceFixe {

	file, _ := ioutil.ReadFile("./assets/public/lista_coduri_mijloace_fixe.json")

	data := []CodMijloaceFixe{}

	err := json.Unmarshal([]byte(file), &data)
	if err != nil {
		log.Panicln(err)
	}

	return data

}
