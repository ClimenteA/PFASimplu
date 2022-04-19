package registre

import (
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/incasari"
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

func CalculeazaPlatiCatreStat(totalIncasariNet float64) float64 {
	return 0.0
}
