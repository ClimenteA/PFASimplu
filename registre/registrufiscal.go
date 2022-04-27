package registre

import (
	"log"
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

func CreeazaRegistruFiscal(incasari []incasari.Factura, cheltuieli []cheltuieli.Cheltuiala) []RegistruFiscal {

	calculIncasari := map[int]float64{}
	for _, data := range incasari {

		ti, err := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		calculIncasari[ti.Year()] = calculIncasari[ti.Year()] + data.SumaIncasata

	}

	calculCheltuieli := map[int]float64{}
	for _, data := range cheltuieli {

		ti, err := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		calculCheltuieli[ti.Year()] = calculCheltuieli[ti.Year()] + data.SumaCheltuita

	}


	

	// fiscal := []RegistruFiscal{}
	// count := 1
	// for _, data := range cheltuieli {
	// 	if data.ObiectInventar || data.MijlocFix {
	// 		obiect := RegistruFiscal{
	// 			NrCrt:             count,
	// 			ElemDeCalculVenit: data.NumeCheltuiala,
	// 			ValoareRon:        data.SumaCheltuita,
	// 			Anul:              data.SumaCheltuita,
	// 		}
	// 		fiscal = append(fiscal, obiect)
	// 		count += 1
	// 	}
	// }

	// return fiscal

	// sort.Slice(sliceJurnal, func(i, j int) bool {

	// 	ti, err := time.Parse(time.RFC3339, sliceJurnal[i].Data+"T00:00:00Z")
	// 	if err != nil {
	// 		log.Panic(err)
	// 	}

	// 	tj, err := time.Parse(time.RFC3339, sliceJurnal[j].Data+"T00:00:00Z")
	// 	if err != nil {
	// 		log.Panic(err)
	// 	}

	// 	return ti.Before(tj)
	// })

}
