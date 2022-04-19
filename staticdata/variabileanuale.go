package staticdata

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
)

type ConfigDetails struct {
	An      int `json:"an"`
	Valoare int `json:"valoare"`
}

type Config struct {
	PragMijlocFix []ConfigDetails `json:"prag_mijloc_fix"`
	EuroToRon     []ConfigDetails `json:"euro_to_ron"`
	SalariiMinime []ConfigDetails `json:"salarii_minime"`
}

func LoadVariabileAnuale() Config {

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
