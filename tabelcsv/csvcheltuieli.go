package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
)

func CreeazaCheltuieliCSV(path, filterYear string, cheltuieli []types.Cheltuiala) types.CaleFisier {

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
			//"Nr Inventar",
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
			"Scos din uz",
			"Modalitate iesire din uz",
			"Data iesire din uz",
			"Document justificativ",
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

		scosDinUz := "Nu"
		if cheltuiala.ScosDinUz {
			scosDinUz = "Da"
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
			//strconv.Itoa(cheltuiala.DetaliiMijlocFix.NrInventar),
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
			scosDinUz,
			cheltuiala.DetaliiIesireDinUz.ModalidateIesireDinUz,
			cheltuiala.DetaliiIesireDinUz.DataIesireDinUz,
			cheltuiala.DetaliiIesireDinUz.CaleDovadaIesireDinUz,
		})
	}

	csvPath := filepath.Join(path, filterYear+"_cheltuieli.csv")
	csvfile, err := os.Create(csvPath)

	if err != nil {
		log.Fatalf("failed creating file: %s", err)
	}

	csvwriter := csv.NewWriter(csvfile)

	for _, row := range rows {
		_ = csvwriter.Write(row)
	}

	csvwriter.Flush()
	csvfile.Close()

	xlsxPath := filepath.Join(path, filterYear+"_cheltuieli.xlsx")
	err = utils.GenerateXLSXFromCSV(csvPath, xlsxPath, ',')
	if err != nil {
		log.Println(err)
	}

	paths := types.CaleFisier{
		XLSX: xlsxPath,
		CSV:  csvPath,
	}

	return paths

}
