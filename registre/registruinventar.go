package registre

import (
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/types"
)

func CreeazaRegistruInventar(cheltuieli []cheltuieli.Cheltuiala) []types.RegistruInventar {

	inventar := []types.RegistruInventar{}
	count := 1
	for _, data := range cheltuieli {
		if data.ObiectInventar || data.MijlocFix {
			obiect := types.RegistruInventar{
				NrCrt:            count,
				DenumireaElemInv: data.NumeCheltuiala,
				ValInvRon:        data.SumaCheltuita,
			}
			inventar = append(inventar, obiect)
			count += 1
		}
	}

	return inventar
}
