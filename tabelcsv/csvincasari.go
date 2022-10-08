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

func CreeazaIncasariCSV(path, filterYear string, incasari []types.FacturaPlusExtraIncasari) types.CaleFisier {

	rows := [][]string{
		{
			"Sursa venit",
			"Serie",
			"Numar",
			"Data",
			"Suma Incasata",
			"Tip Tranzactie",
			"Cale Fisier",
		},
	}

	for _, incasare := range incasari {
		rows = append(rows, []string{
			incasare.SursaVenit,
			incasare.Serie,
			strconv.Itoa(incasare.Numar),
			incasare.Data,
			fmt.Sprintf("%.2f", incasare.SumaIncasata),
			incasare.TipTranzactie,
			incasare.CaleIncasare,
		})
	}

	csvPath := filepath.Join(path, filterYear+"_incasari.csv")
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

	xlsxPath := filepath.Join(path, filterYear+"_incasari.xlsx")
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
