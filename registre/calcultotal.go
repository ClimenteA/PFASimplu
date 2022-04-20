package registre

import (
	"log"

	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
)

func CalculeazaIncasariBrut(incasari []incasari.Factura) float64 {

	total := 0.0
	for _, data := range incasari {
		total = total + data.SumaIncasata
	}

	return total

}

func CalculeazaCheltuieliDeductibile(cheltuieli []cheltuieli.Cheltuiala) float64 {

	total := 0.0
	for _, data := range cheltuieli {
		total = total + data.SumaCheltuita
	}

	return total

}

func CalculeazaPlatiCatreStat(totalIncasariNet float64, anul string) float64 {

	anualVars := staticdata.LoadVariabileAnuale()

	log.Println("CalculeazaPlatiCatreStat", anualVars)

	// https://static.anaf.ro/static/10/Anaf/formulare/Instructiuni_D_212_OPANAF_14_2021.pdf

	// Impozit anual pe venit
	// 10%

	// Contributia de asigurari sociale (CAS) Pensie
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 25%

	// Contributia de asigurari sociale de sanatate (CASS) - Sanatate
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 10%

	return 0.0

}
