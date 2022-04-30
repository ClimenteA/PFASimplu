package registre

import (
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
)

func CreeazaRegistruInventar(cheltuieli []cheltuieli.Cheltuiala) []types.RegistruInventar {

	mijloaceFixeSalvate := []string{}
	inventar := []types.RegistruInventar{}
	count := 1
	for _, data := range cheltuieli {

		if data.ObiectInventar {
			obiect := types.RegistruInventar{
				NrCrt:            count,
				DenumireaElemInv: data.NumeCheltuiala,
				ValInvRon:        data.SumaCheltuita,
				CaleCheltuiala:   data.CaleCheltuiala,
			}
			inventar = append(inventar, obiect)

			count += 1

		}

		if data.MijlocFix {

			metadataPath := filepath.Join(filepath.Dir(data.CaleCheltuiala), "metadata.json")

			if !utils.SliceContains(mijloaceFixeSalvate, metadataPath) {

				expense := getExpenseMetadata(metadataPath)

				obiect := types.RegistruInventar{
					NrCrt:            count,
					DenumireaElemInv: expense.NumeCheltuiala,
					ValInvRon:        expense.SumaCheltuita,
					CaleCheltuiala:   data.CaleCheltuiala,
				}

				inventar = append(inventar, obiect)
				mijloaceFixeSalvate = append(mijloaceFixeSalvate, metadataPath)
				count += 1
			}

		}

	}

	return inventar
}
