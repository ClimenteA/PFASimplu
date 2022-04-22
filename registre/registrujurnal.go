package registre

import (
	"log"
	"sort"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/incasari"
)

type RegistruJurnal struct {
	NrCrt                      int     `json:"nr_crt"`
	Data                       string  `json:"data"`
	DocumentFelNr              string  `json:"document_fel_numar"`
	FelulOperatiuniiExplicatii string  `json:"felul_operatiunii_explicatii"`
	IncasariNumerar            float64 `json:"incasari_numerar"`
	IncasariBanca              float64 `json:"incasari_banca"`
	PlatiNumerar               float64 `json:"plati_numerar"`
	PlatiBanca                 float64 `json:"PlatiBanca"`
}

func processIncasari(sliceJurnal []RegistruJurnal, incasari []incasari.Factura) []RegistruJurnal {

	for _, incasare := range incasari {
		registruJurnal := RegistruJurnal{
			Data:                       incasare.Data,
			DocumentFelNr:              incasare.CaleFactura,
			FelulOperatiuniiExplicatii: "Incasare " + incasare.Serie + strconv.Itoa(incasare.Numar),
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

func processCheltuieli(sliceJurnal []RegistruJurnal, cheltuieli []cheltuieli.Cheltuiala) []RegistruJurnal {

	for _, cheltuiala := range cheltuieli {
		registruJurnal := RegistruJurnal{
			Data:                       cheltuiala.Data,
			DocumentFelNr:              cheltuiala.CaleCheltuiala,
			FelulOperatiuniiExplicatii: "Cheltuiala " + cheltuiala.NumeCheltuiala,
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

func addNrCrt(sliceJurnal []RegistruJurnal) []RegistruJurnal {

	count := 1
	sliceJurnalNrCrt := []RegistruJurnal{}
	for _, data := range sliceJurnal {
		data.NrCrt = count
		count = count + 1
		sliceJurnalNrCrt = append(sliceJurnalNrCrt, data)
	}

	return sliceJurnalNrCrt

}

func sortByDate(sliceJurnal []RegistruJurnal) []RegistruJurnal {

	sort.Slice(sliceJurnal, func(i, j int) bool {

		ti, err := time.Parse(time.RFC3339, sliceJurnal[i].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, sliceJurnal[j].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		return ti.Before(tj)
	})

	return sliceJurnal

}

func CreeazaRegistruJurnal(incasari []incasari.Factura, cheltuieli []cheltuieli.Cheltuiala) []RegistruJurnal {

	sliceJurnal := []RegistruJurnal{}
	sliceJurnal = processIncasari(sliceJurnal, incasari)
	sliceJurnal = processCheltuieli(sliceJurnal, cheltuieli)
	sliceJurnal = sortByDate(sliceJurnal)
	sliceJurnal = addNrCrt(sliceJurnal)

	return sliceJurnal

}
