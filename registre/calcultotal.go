package registre

import (
	"strconv"

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

	// https://static.anaf.ro/static/10/Anaf/formulare/Instructiuni_D_212_OPANAF_14_2021.pdf

	// Impozit anual pe venit
	// 10%

	// Contributia de asigurari sociale (CAS) Pensie
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 25%

	// Contributia de asigurari sociale de sanatate (CASS) - Sanatate
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 10%

	anualVars := staticdata.LoadVariabileAnuale()

	salariulMinim := 0.0
	for idx, data := range anualVars.SalariiMinime {
		strAn := strconv.Itoa(data.An)
		if strAn == anul {
			salariulMinim = float64(anualVars.SalariiMinime[idx].Valoare)
			break
		}
	}

	plafonTaxe := salariulMinim * 12

	impozitPeVenit := 0.0
	pensie := 0.0
	sanatate := 0.0

	if totalIncasariNet >= plafonTaxe {
		impozitPeVenit = 10 * plafonTaxe / 100
		pensie = 25 * totalIncasariNet / 100
		sanatate = 10 * totalIncasariNet / 100
	}

	taxes := impozitPeVenit + pensie + sanatate

	return taxes

}
