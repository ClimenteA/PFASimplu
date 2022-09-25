package registre

import (
	"log"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func calculIncasariAn(incasari []types.FacturaPlusExtraIncasari) map[string]float64 {

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

func calculIncasariGrupateAn(incasari []types.FacturaPlusExtraIncasari) map[string]float64 {

	calculIncasari := map[string]float64{}
	for _, data := range incasari {

		ti, err := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}
		anul := strconv.Itoa(ti.Year())
		key := anul + ":__:" + data.SursaVenit
		calculIncasari[key] = calculIncasari[key] + data.SumaIncasata

	}

	return calculIncasari
}

func calculCheltuieliAn(cheltuieli []types.Cheltuiala) map[string]float64 {

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

func addNrCrtRegFiscal(registruFiscal []types.RegistruFiscal) []types.RegistruFiscal {

	count := 1
	dataslice := []types.RegistruFiscal{}
	for _, data := range registruFiscal {
		data.NrCrt = count
		count = count + 1
		dataslice = append(dataslice, data)
	}

	return dataslice

}

func CreeazaRegistruFiscal(
	aniInregistrati []string,
	incasari []types.FacturaPlusExtraIncasari,
	cheltuieli []types.Cheltuiala,
	filterYear string) []types.RegistruFiscal {

	calculIncasari := calculIncasariAn(incasari)
	calculIncasariGrupate := calculIncasariGrupateAn(incasari)
	calculCheltuieli := calculCheltuieliAn(cheltuieli)

	registruFiscal := []types.RegistruFiscal{}
	for _, anul := range aniInregistrati {

		if filterYear == anul {
			anulInt, _ := strconv.Atoi(anul)

			for key, incasareGrup := range calculIncasariGrupate {

				anulSursa := strings.Split(key, ":__:")
				anulGroup, _ := strconv.Atoi(anulSursa[0])

				dateIncasariAn := types.RegistruFiscal{
					ElemDeCalculVenit: anulSursa[1],
					ValoareRon:        incasareGrup,
					Anul:              anulGroup,
				}

				registruFiscal = append(registruFiscal, dateIncasariAn)

			}

			dateIncasariAn := types.RegistruFiscal{
				ElemDeCalculVenit: "Total Incasari",
				ValoareRon:        calculIncasari[anul],
				Anul:              anulInt,
			}

			dateCheltuieliAn := types.RegistruFiscal{
				ElemDeCalculVenit: "Total cheltuieli",
				ValoareRon:        calculCheltuieli[anul],
				Anul:              anulInt,
			}

			registruFiscal = append(registruFiscal, dateIncasariAn)
			registruFiscal = append(registruFiscal, dateCheltuieliAn)

		}
	}

	sort.Slice(registruFiscal, func(i, j int) bool {
		return registruFiscal[i].Anul < registruFiscal[j].Anul
	})

	registruFiscal = addNrCrtRegFiscal(registruFiscal)

	return registruFiscal

}
