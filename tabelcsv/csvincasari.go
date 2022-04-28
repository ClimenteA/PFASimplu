package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/incasari"
)

func CreeazaIncasariCSV(path string, incasari []incasari.Factura) {

	rows := [][]string{
		{
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
			incasare.Serie,
			strconv.Itoa(incasare.Numar),
			incasare.Data,
			fmt.Sprintf("%.2f", incasare.SumaIncasata),
			incasare.TipTranzactie,
			incasare.CaleFactura,
		})
	}

	csvfile, err := os.Create(filepath.Join(path, "incasari.csv"))

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
