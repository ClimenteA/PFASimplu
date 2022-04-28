package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"strconv"

	"log"
	"os"
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func CreeazaRegistruInventarCSV(path string, registruInventar []types.RegistruInventar) {

	rows := [][]string{
		{
			"Nr.Crt.",
			"Denumirea elementelor inventariate",
			"Valoarea de inventar (RON)",
		},
	}

	for _, inventar := range registruInventar {
		rows = append(rows, []string{
			strconv.Itoa(inventar.NrCrt),
			inventar.DenumireaElemInv,
			fmt.Sprintf("%.2f", inventar.ValInvRon),
		})
	}

	csvfile, err := os.Create(filepath.Join(path, "registru_inventar.csv"))

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
