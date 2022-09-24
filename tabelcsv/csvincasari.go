package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func CreeazaIncasariCSV(path, filterYear string, incasari []types.FacturaPlusExtraIncasari) string {

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

	// serie := "-"
	// if incasare.Serie != "" {
	// 	serie = incasare.Serie
	// }

	// numar := "-"
	// if incasare.Numar > 0 {
	// 	numar = strconv.Itoa(incasare.Numar)
	// }

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

	return csvPath
}
