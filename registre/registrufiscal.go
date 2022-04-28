package registre

import (
	"log"
	"sort"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/incasari"
)

type RegistruFiscal struct {
	NrCrt             int     `json:"nr_crt"`
	ElemDeCalculVenit string  `json:"elemente_de_calcul_pentru_stabilirea_venitului_net_anual_pierderi_nete_anuale"`
	ValoareRon        float64 `json:"valoarea_ron"`
	Anul              int     `json:"anul"`
}

func calculIncasariAn(incasari []incasari.Factura) map[string]float64 {

	calculIncasari := map[string]float64{}
	for _, data := range incasari {

		ti, err := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}
		anul := strconv.Itoa(ti.Year())

		calculIncasari[anul] = calculIncasari[anul] + data.SumaIncasata

	}

	return calculIncasari
}

func calculCheltuieliAn(cheltuieli []cheltuieli.Cheltuiala) map[string]float64 {

	calculCheltuieli := map[string]float64{}
	for _, data := range cheltuieli {

		ti, err := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}
		anul := strconv.Itoa(ti.Year())

		calculCheltuieli[anul] = calculCheltuieli[anul] + data.SumaCheltuita

	}

	return calculCheltuieli

}

func CreeazaRegistruFiscal(aniInregistrati []string, incasari []incasari.Factura, cheltuieli []cheltuieli.Cheltuiala) []RegistruFiscal {

	calculIncasari := calculIncasariAn(incasari)
	calculCheltuieli := calculCheltuieliAn(cheltuieli)

	count := 1
	registruFiscal := []RegistruFiscal{}
	for _, anul := range aniInregistrati {

		anulInt, _ := strconv.Atoi(anul)

		dateIncasariAn := RegistruFiscal{
			NrCrt:             count,
			ElemDeCalculVenit: "Total incasari",
			ValoareRon:        calculIncasari[anul],
			Anul:              anulInt,
		}

		count += 1

		dateCheltuieliAn := RegistruFiscal{
			NrCrt:             count,
			ElemDeCalculVenit: "Total cheltuieli",
			ValoareRon:        calculCheltuieli[anul],
			Anul:              anulInt,
		}

		count += 1

		registruFiscal = append(registruFiscal, dateIncasariAn)
		registruFiscal = append(registruFiscal, dateCheltuieliAn)

	}

	sort.Slice(registruFiscal, func(i, j int) bool {
		return registruFiscal[i].Anul > registruFiscal[j].Anul
	})

	return registruFiscal

}
