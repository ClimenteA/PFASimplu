package tabelpdf

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func CreeazaRegistruJurnalCSV(path, filterYear string, registruJurnal []types.RegistruJurnal) string {

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

	for _, incasare := range registruJurnal {

		rows = append(rows, []string{
			strconv.Itoa(incasare.NrCrt),
			incasare.Data,
			incasare.DocumentFelNr,
			incasare.FelulOperatiuniiExplicatii,
			fmt.Sprintf("%.2f", incasare.IncasariNumerar),
			fmt.Sprintf("%.2f", incasare.IncasariBanca),
			fmt.Sprintf("%.2f", incasare.PlatiNumerar),
			fmt.Sprintf("%.2f", incasare.PlatiBanca),
		})
	}

	csvPath := filepath.Join(path, filterYear+"_registru_jurnal.csv")
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
