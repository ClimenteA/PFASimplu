package staticdata

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
)

type ConfigDetails struct {
	An      int     `json:"an"`
	Valoare float64 `json:"valoare"`
}

type Config struct {
	VersiuneAplicatie string          `json:"versiune_aplicatie"`
	PragMijlocFix     []ConfigDetails `json:"prag_mijloc_fix"`
	EuroToRon         []ConfigDetails `json:"euro_to_ron"`
	SalariiMinime     []ConfigDetails `json:"salarii_minime"`
	PlafonTVA         []ConfigDetails `json:"plafon_tva"`
	Port              string          `json:"port"`
	Environment       string          `json:"environment"`
}

func LoadPFAConfig() Config {

	var data Config

	jsonFile, err := os.Open("./assets/public/pfaconfig.json")
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}
