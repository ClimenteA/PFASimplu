package registre

import "github.com/ClimenteA/pfasimplu-go/cheltuieli"

type RegistruInventar struct {
	NrCrt            int     `json:"nr_crt"`
	DenumireaElemInv string  `json:"denumirea_elementelor_inventariate"`
	ValInvRon        float64 `json:"valoarea_de_inventar_ron"`
}

func CreeazaRegistruInventar(cheltuieli []cheltuieli.Cheltuiala) []RegistruInventar {

	inventar := []RegistruInventar{}
	count := 1
	for _, data := range cheltuieli {
		if data.ObiectInventar || data.MijlocFix {
			obiect := RegistruInventar{
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
