package utils

import (
	"encoding/csv"
	"log"
	"os"

	"github.com/tealeg/xlsx"
)

func GenerateXLSXFromCSV(csvPath string, XLSXPath string, delimiter rune) error {

	csvFile, err := os.Open(csvPath)
	if err != nil {
		return err
	}
	defer csvFile.Close()
	reader := csv.NewReader(csvFile)
	reader.Comma = delimiter
	rows, err := reader.ReadAll()
	if err != nil {
		log.Fatal(err)
	}

	xlsxFile := xlsx.NewFile()
	sheet, err := xlsxFile.AddSheet("sheet")
	if err != nil {
		return err
	}
	for _, cells := range rows {
		row := sheet.AddRow()
		for _, cell := range cells {
			xlcell := row.AddCell()
			xlcell.Value = cell
		}
	}

	return xlsxFile.Save(XLSXPath)
}
