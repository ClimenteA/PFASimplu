package registre

import (
	"log"
	"path/filepath"
	"sort"
	"time"

	output "github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
)

func sortByDateRI(sliceInventar []types.RegistruInventar) []types.RegistruInventar {

	sort.Slice(sliceInventar, func(i, j int) bool {

		ti, err := time.Parse(time.RFC3339, sliceInventar[i].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, sliceInventar[j].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		return ti.Before(tj)
	})

	return sliceInventar

}

func addNrCrtRI(sliceInventar []types.RegistruInventar) []types.RegistruInventar {

	count := 1
	sliceInventarNrCrt := []types.RegistruInventar{}
	for _, data := range sliceInventar {
		data.NrCrt = count
		count = count + 1
		sliceInventarNrCrt = append(sliceInventarNrCrt, data)
	}

	return sliceInventarNrCrt

}

func CreeazaRegistruInventar(cheltuieli []types.Cheltuiala) []types.RegistruInventar {

	mijloaceFixeSalvate := []string{}
	inventar := []types.RegistruInventar{}
	for _, data := range cheltuieli {

		if data.ObiectInventar {
			obiect := types.RegistruInventar{
				DenumireaElemInv: data.NumeCheltuiala,
				ValInvRon:        data.SumaCheltuita,
				CaleCheltuiala:   data.CaleCheltuiala,
				Data:             data.Data,
				MijlocFix:        false,
			}
			inventar = append(inventar, obiect)
		}

		if data.MijlocFix {

			metadataPath := filepath.Join(filepath.Dir(data.CaleCheltuiala), "metadata.json")

			if !utils.SliceContains(mijloaceFixeSalvate, metadataPath) {

				expense := output.GetExpenseMetadata(metadataPath)

				obiect := types.RegistruInventar{
					DenumireaElemInv: expense.NumeCheltuiala,
					ValInvRon:        expense.SumaCheltuita,
					CaleCheltuiala:   data.CaleCheltuiala,
					Data:             data.DetaliiMijlocFix.DataPuneriiInFunctiune,
					MijlocFix:        true,
				}

				inventar = append(inventar, obiect)
				mijloaceFixeSalvate = append(mijloaceFixeSalvate, metadataPath)
			}

		}

	}

	inventar = sortByDateRI(inventar)
	inventar = addNrCrtRI(inventar)

	return inventar
}
