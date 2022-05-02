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

func CreeazaRegistruFiscalCSV(path, filterYear string, registruFiscal []types.RegistruFiscal) string {

	rows := [][]string{
		{
			"Nr.Crt.",
			"Elemente de calcul pentru stabilirea venitului net annual/pierderii nete anuale",
			"Valoare (RON)",
			"Anul",
		},
	}

	for _, fiscal := range registruFiscal {
		rows = append(rows, []string{
			strconv.Itoa(fiscal.NrCrt),
			fiscal.ElemDeCalculVenit,
			fmt.Sprintf("%.2f", fiscal.ValoareRon),
			strconv.Itoa(fiscal.Anul),
		})
	}

	csvPath := filepath.Join(path, filterYear+"_registru_fiscal.csv")
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
