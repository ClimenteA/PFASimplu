package tabelcsv

import (
	"encoding/csv"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"

	"log"
	"os"
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
)

func CreeazaRegistruInventarCSV(path, filterYear string, registruInventar []types.RegistruInventar) types.CaleFisier {

	if _, err := os.Stat(path); err != nil || !os.IsExist(err) {
		os.MkdirAll(path, 0750)
	}

	rows := [][]string{
		{
			"Nr.Crt.",
			"Denumirea elementelor inventariate",
			"Valoarea de inventar (RON)",
			"Data",
			"Stocare",
			"MijlocFix",
			"Scos din uz",
			"Modalitate iesire din uz",
			"Data iesire din uz",
			"Document justificativ",
		},
	}

	for _, inventar := range registruInventar {

		var mijlocFix string
		if inventar.MijlocFix {
			mijlocFix = "Da"
		} else {
			mijlocFix = "Nu"
		}

		var scosDinUz string
		if inventar.ScosDinUz {
			scosDinUz = "Da"
		} else {
			scosDinUz = "Nu"
		}

		rows = append(rows, []string{
			strconv.Itoa(inventar.NrCrt),
			inventar.DenumireaElemInv,
			fmt.Sprintf("%.2f", inventar.ValInvRon),
			inventar.Data,
			inventar.CaleCheltuiala,
			mijlocFix,
			scosDinUz,
			inventar.ModalitateIesireDinUz,
			inventar.DataIesireDinUz,
			inventar.CaleDovadaIesireDinUz,
		})
	}

	csvPath := filepath.Join(path, filterYear+"registru_inventar.csv")
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

	xlsxPath := filepath.Join(path, filterYear+"registru_inventar.xlsx")
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

func getFisiereRegistruInventar(root string) ([]string, error) {

	allFiles := []string{}
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if !info.IsDir() {
			if strings.HasSuffix(path, "_registru_inventar.csv") && !strings.Contains(path, "registre") {
				allFiles = append(allFiles, path)
			}
		}
		return nil
	})

	if err != nil {
		panic(err)
	}

	sort.Slice(allFiles, func(i, j int) bool {

		// Get year and form date for sorting from "/etc/path/2020_registru_inventar.csv"
		iDate := filepath.Base(allFiles[i])[0:4] + "-01-01T00:00:00Z"
		jDate := filepath.Base(allFiles[j])[0:4] + "-01-01T00:00:00Z"

		ti, err := time.Parse(time.RFC3339, iDate)
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, jDate)
		if err != nil {
			log.Panic(err)
		}

		return ti.Before(tj)
	})

	return allFiles, err
}

func parseRegistruInventar(data [][]string) []types.RegistruInventar {

	registruInventar := []types.RegistruInventar{}

	for i, line := range data {

		if i == 0 {
			continue
		}

		// "Nr.Crt.",
		// "Denumirea elementelor inventariate",
		// "Valoarea de inventar (RON)",
		// "Data",
		// "Stocare",
		// "MijlocFix",
		// "Scos din uz",
		// "Modalitate iesire din uz",
		// "Data iesire din uz",
		// "Document justificativ",
		row := types.RegistruInventar{}
		for j, field := range line {

			if j == 1 {
				row.DenumireaElemInv = field
			}

			if j == 2 {

				val, err := strconv.ParseFloat(field, 64)
				if err != nil {
					log.Panicln(err)
				}
				row.ValInvRon = val
			}

			if j == 3 {
				row.Data = field
			}

			if j == 4 {
				row.CaleCheltuiala = field
			}

			if j == 5 {
				if field == "Da" {
					row.MijlocFix = true
				}
				if field == "Nu" {
					row.MijlocFix = false
				}
			}

			if j == 6 {
				if field == "Da" {
					row.ScosDinUz = true
				}
				if field == "Nu" {
					row.ScosDinUz = false
				}
			}

			if j == 7 {
				row.ModalitateIesireDinUz = field
			}

			if j == 8 {
				row.DataIesireDinUz = field
			}

			if j == 9 {
				row.CaleDovadaIesireDinUz = field
			}

		}

		registruInventar = append(registruInventar, row)

	}

	return registruInventar
}

func addNrCrt(sliceInventar []types.RegistruInventar) []types.RegistruInventar {

	count := 1
	sliceInventarNrCrt := []types.RegistruInventar{}
	for _, data := range sliceInventar {
		data.NrCrt = count
		count = count + 1
		sliceInventarNrCrt = append(sliceInventarNrCrt, data)
	}

	return sliceInventarNrCrt

}

func FullRegistruInventar(path, filterYear string) []types.RegistruInventar {

	pathsRegistruInventar, err := getFisiereRegistruInventar(path)
	if err != nil {
		panic(err)
	}

	registruInventar := []types.RegistruInventar{}
	for _, path := range pathsRegistruInventar {

		f, err := os.Open(path)
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()

		csvReader := csv.NewReader(f)
		csvReader.Comma = ','
		data, err := csvReader.ReadAll()
		if err != nil {
			log.Fatal(err)
		}

		registruInventar = append(registruInventar, parseRegistruInventar(data)...)

	}

	registruInventar = addNrCrt(registruInventar)

	return registruInventar

}
