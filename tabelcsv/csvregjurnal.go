package tabelcsv

import (
	"encoding/csv"
	"log"
	"os"
	"path/filepath"
)

func CreeazaRegistruJurnalCSV(path string) {

	rows := [][]string{
		{
			"Nr.Crt.",
			"Data",
			"Documentul (fel, numar)",
			"Felul operatiunii (explicatii)",
			"Incasari Numerar",
			"Incasari Banca",
			"Plati Numerar",
			"Plati Banca",
		},
	}

	for _, incasare := range []string{} {
		rows = append(rows, []string{
			incasare,
		})
	}

	csvfile, err := os.Create(filepath.Join(path, ".csv"))

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
