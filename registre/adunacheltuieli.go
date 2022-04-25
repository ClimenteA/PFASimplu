package registre

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
)

func getCheltuieliJsonPaths(user auth.Account) ([]string, error) {

	cheltuieliMetadataJson := []string{}

	err := filepath.Walk(user.StocareCheltuieli,
		func(path string, _ os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if strings.Contains(path, "metadata.json") {
				cheltuieliMetadataJson = append(cheltuieliMetadataJson, path)
			}

			return nil
		})
	if err != nil {
		log.Panicln(err)
	}

	return cheltuieliMetadataJson, err

}

func getExpenseMetadata(path string) cheltuieli.Cheltuiala {

	var data cheltuieli.Cheltuiala

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func getExpensesDataSlice(cheltuieliMetadataJson []string, anul string) []cheltuieli.Cheltuiala {

	expenses := []cheltuieli.Cheltuiala{}

	for _, path := range cheltuieliMetadataJson {
		expense := getExpenseMetadata(path)
		if strings.HasPrefix(expense.Data, anul) {
			expenses = append(expenses, expense)
		}
	}

	sort.Slice(expenses, func(i, j int) bool {

		ti, err := time.Parse(time.RFC3339, expenses[i].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, expenses[j].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		return ti.After(tj)
	})

	return expenses

}

func AdunaCheltuieli(user auth.Account, anul string) []cheltuieli.Cheltuiala {

	cheltuieliMetadataJson, err := getCheltuieliJsonPaths(user)
	if err != nil {
		panic(err)
	}

	expenses := getExpensesDataSlice(cheltuieliMetadataJson, anul)

	return expenses
}