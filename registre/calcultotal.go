package registre

import (
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/ClimenteA/pfasimplu-go/types"
)

func CalculeazaIncasariBrut(incasari []types.Factura) float64 {

	total := 0.0
	for _, data := range incasari {
		total = total + data.SumaIncasata
	}

	return total

}

func CalculeazaCheltuieliDeductibile(cheltuieli []types.Cheltuiala) float64 {

	total := 0.0
	for _, data := range cheltuieli {
		total = total + data.SumaCheltuita
	}
	return total

}

func CalculPlatiAnaf(declaratii []declaratii.Declaratie) float64 {

	total := 0.0
	for _, data := range declaratii {
		total = total + data.PlataAnaf
	}
	return total
}

func CalculeazaPlatiCatreStat(totalIncasariNet, platiAnaf float64, anul string) float64 {

	// https://startco.ro/blog/taxe-pfa/

	// Impozit anual pe venit
	// 10% din venitul net

	// Contributia de asigurari sociale (CAS) Pensie
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 25% din salariulMinim * 12

	// Contributia de asigurari sociale de sanatate (CASS) - Sanatate
	// Nu se plateste daca venitul net este mai mic sau egal cu 12 salarii minime brute (2300 RON in 2021)
	// 10% din salariulMinim * 12

	anualVars := staticdata.LoadPFAConfig()

	salariulMinim := 0.0
	for idx, data := range anualVars.SalariiMinime {
		strAn := strconv.Itoa(data.An)
		if strAn == anul {
			salariulMinim = float64(anualVars.SalariiMinime[idx].Valoare)
			break
		}
	}

	pragulMinim := salariulMinim * 12
	impozitPeVenit := 10 * totalIncasariNet / 100

	pensie := 0.0
	sanatate := 0.0

	if totalIncasariNet >= pragulMinim {
		pensie = 25 * pragulMinim / 100
		sanatate = 10 * pragulMinim / 100
	}

	allTaxes := impozitPeVenit + pensie + sanatate
	remainingTaxes := allTaxes - platiAnaf

	// if remainingTaxes < 0 {
	// 	remainingTaxes = 0
	// }

	return remainingTaxes

}
