package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
)

func CreeazaCheltuieliCSV(path string, cheltuieli []cheltuieli.Cheltuiala) {

	rows := [][]string{
		{
			"Nume Cheltuiala",
			"Suma Cheltuita",
			"Tip Tranzactie",
			"Data",
			"Obiect Inventar",
			"Mijloc Fix",
			"Ani Amortizare",
			"Data Punerii In Functiune",
			"Cod Clasificare",
			"Nr Inventar",
			"Fel Serie Numar Data Document",
			"Valoare Inventar",
			"Amortizare Lunara",
			"Denumire Si Caracteristici",
			"Accesorii",
			"Grupa",
			"Anul Darii In Folosinta",
			"Luna Darii In Folosinta",
			"Anul Amortizarii Complete",
			"Luna Amortizarii Complete",
			"Durata Normala De Functionare",
			"Cota De Amortizare",
			"Cale Fisier",
		},
	}

	for _, cheltuiala := range cheltuieli {

		obiectDeInventar := "Nu"
		if cheltuiala.ObiectInventar {
			obiectDeInventar = "Da"
		}

		mijlocFix := "Nu"
		if cheltuiala.MijlocFix {
			mijlocFix = "Da"
		}

		rows = append(rows, []string{
			cheltuiala.NumeCheltuiala,
			fmt.Sprintf("%f", cheltuiala.SumaCheltuita),
			cheltuiala.TipTranzactie,
			cheltuiala.Data,
			obiectDeInventar,
			mijlocFix,
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.AniAmortizare),
			cheltuiala.DetaliiMijlocFix.DataPuneriiInFunctiune,
			cheltuiala.DetaliiMijlocFix.CodClasificare,
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.NrInventar),
			cheltuiala.DetaliiMijlocFix.FelSerieNumarDataDocument,
			fmt.Sprintf("%f", cheltuiala.DetaliiMijlocFix.ValoareInventar),
			fmt.Sprintf("%f", cheltuiala.DetaliiMijlocFix.AmortizareLunara),
			cheltuiala.DetaliiMijlocFix.DenumireSiCaracteristici,
			cheltuiala.DetaliiMijlocFix.Accesorii,
			cheltuiala.DetaliiMijlocFix.Grupa,
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.AnulDariiInFolosinta),
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.LunaDariiInFolosinta),
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.AnulAmortizariiComplete),
			strconv.Itoa(cheltuiala.DetaliiMijlocFix.LunaAmortizariiComplete),
			cheltuiala.DetaliiMijlocFix.DurataNormalaDeFunctionare,
			fmt.Sprintf("%f", cheltuiala.DetaliiMijlocFix.CotaDeAmortizare),
			cheltuiala.CaleCheltuiala,
		})
	}

	csvfile, err := os.Create(filepath.Join(path, "cheltuieli.csv"))

	if err != nil {
		log.Fatalf("failed creating file: %s", err)
	}

	csvwriter := csv.NewWriter(csvfile)

	for _, row := range rows {
		_ = csvwriter.Write(row)
	}

	csvwriter.Flush()
	csvfile.Close()
}
