package registre

import (
	"log"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func processIncasari(sliceJurnal []types.RegistruJurnal, incasari []types.FacturaPlusExtraIncasari) []types.RegistruJurnal {

	for _, incasare := range incasari {

		registruJurnal := types.RegistruJurnal{}

		if strings.HasPrefix(incasare.CaleFactura, "Total luna") {

			registruJurnal = types.RegistruJurnal{
				Total:                      true,
				Data:                       incasare.Data,
				DocumentFelNr:              incasare.CaleFactura,
				FelulOperatiuniiExplicatii: incasare.Serie,
			}

		} else {

			registruJurnal = types.RegistruJurnal{
				Data:                       incasare.Data,
				DocumentFelNr:              incasare.CaleFactura,
				FelulOperatiuniiExplicatii: "Incasare " + incasare.Serie + strconv.Itoa(incasare.Numar),
			}

		}

		if incasare.TipTranzactie == "NUMERAR" {
			registruJurnal.IncasariNumerar = incasare.SumaIncasata
		} else {
			registruJurnal.IncasariBanca = incasare.SumaIncasata
		}

		sliceJurnal = append(sliceJurnal, registruJurnal)
	}

	return sliceJurnal

}

func processCheltuieli(sliceJurnal []types.RegistruJurnal, cheltuieli []types.Cheltuiala) []types.RegistruJurnal {

	for _, cheltuiala := range cheltuieli {

		registruJurnal := types.RegistruJurnal{}

		if strings.HasPrefix(cheltuiala.CaleCheltuiala, "Total luna") {

			registruJurnal = types.RegistruJurnal{
				Total:                      true,
				Data:                       cheltuiala.Data,
				DocumentFelNr:              cheltuiala.CaleCheltuiala,
				FelulOperatiuniiExplicatii: cheltuiala.NumeCheltuiala,
			}

		} else {

			registruJurnal = types.RegistruJurnal{
				Data:                       cheltuiala.Data,
				DocumentFelNr:              cheltuiala.CaleCheltuiala,
				FelulOperatiuniiExplicatii: "Cheltuiala " + cheltuiala.NumeCheltuiala,
			}

		}

		if cheltuiala.TipTranzactie == "NUMERAR" {
			registruJurnal.PlatiNumerar = cheltuiala.SumaCheltuita
		} else {
			registruJurnal.PlatiBanca = cheltuiala.SumaCheltuita
		}

		sliceJurnal = append(sliceJurnal, registruJurnal)
	}

	return sliceJurnal
}

func addNrCrt(sliceJurnal []types.RegistruJurnal) []types.RegistruJurnal {

	count := 1
	sliceJurnalNrCrt := []types.RegistruJurnal{}
	for _, data := range sliceJurnal {
		data.NrCrt = count
		count = count + 1
		sliceJurnalNrCrt = append(sliceJurnalNrCrt, data)
	}

	return sliceJurnalNrCrt

}

func sortByDate(sliceJurnal []types.RegistruJurnal) []types.RegistruJurnal {

	sort.Slice(sliceJurnal, func(i, j int) bool {

		ti, err := time.Parse(time.RFC3339, sliceJurnal[i].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, sliceJurnal[j].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		// Make sure total is always at the end of month
		sameDate := ti.Equal(tj)
		stocarei := strings.HasPrefix(sliceJurnal[i].DocumentFelNr, "stocare")
		totalj := strings.HasPrefix(sliceJurnal[j].DocumentFelNr, "Total luna")

		if sameDate && !stocarei && !totalj {
			return false
		} else if sameDate && stocarei && totalj {
			return true
		} else {
			return ti.Before(tj)
		}

	})

	return sliceJurnal

}

func CreeazaRegistruJurnal(incasari []types.FacturaPlusExtraIncasari, cheltuieli []types.Cheltuiala) []types.RegistruJurnal {

	sliceJurnal := []types.RegistruJurnal{}
	sliceJurnal = processIncasari(sliceJurnal, incasari)
	sliceJurnal = processCheltuieli(sliceJurnal, cheltuieli)
	sliceJurnal = sortByDate(sliceJurnal)
	sliceJurnal = addNrCrt(sliceJurnal)

	return sliceJurnal

}
