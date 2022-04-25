package extrasbancar

import (
	"encoding/csv"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
)

type ExtrasBancarING struct {
	NumarCont        string  `json:"numar_cont"`
	DataProcesarii   string  `json:"data_procesarii"`
	Suma             float64 `json:"suma"`
	TipTranzactie    string  `json:"tip_tranzactie"`
	NumeBeneficiar   string  `json:"nume_beneficiar"`
	AdresaBeneficiar string  `json:"adresa_beneficiar"`
	SoldIntermediar  float64 `json:"sold_intermediar"`
}

// 0 RO04INGB0000999911194833
// 1 20211122
// 2 -5,00
// 3 RON
// 4 Comision pe operatiune
// 5 ING Bank Romania
// 10 29124,73

func parseExtrasBancar(data [][]string) []ExtrasBancarING {

	var extrasBancar []ExtrasBancarING

	for i, line := range data {

		if i == 0 {
			continue
		}

		row := ExtrasBancarING{}

		for j, field := range line {

			if j == 0 {
				row.NumarCont = field
			} else if j == 1 {

				isodate := field[0:4] + "-" + field[4:6] + "-" + field[6:]
				row.DataProcesarii = isodate

			} else if j == 2 {

				val, err := strconv.ParseFloat(strings.Replace(field, ",", ".", -1), 64)
				if err != nil {
					log.Panicln(err)
				}

				row.Suma = val

			} else if j == 3 {
				row.TipTranzactie = field
			} else if j == 4 {
				row.NumeBeneficiar = field
			} else if j == 5 {
				row.AdresaBeneficiar = field
			} else if j == 10 {

				if val, err := strconv.ParseFloat(field, 64); err == nil {
					row.SoldIntermediar = val
				}

			}

		}

		extrasBancar = append(extrasBancar, row)
	}

	return extrasBancar
}

func DateING(user auth.Account, anul string) [][]ExtrasBancarING {

	extraseBancareMetadata := AdunaExtraseING(user, anul)

	extraseBancare := [][]ExtrasBancarING{}

	for _, e := range extraseBancareMetadata {

		f, err := os.Open(e.CaleDocument)
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()

		csvReader := csv.NewReader(f)
		csvReader.Comma = ';'
		data, err := csvReader.ReadAll()
		if err != nil {
			log.Fatal(err)
		}

		extrasBancar := parseExtrasBancar(data)
		extraseBancare = append(extraseBancare, extrasBancar)
	}

	return extraseBancare
}
