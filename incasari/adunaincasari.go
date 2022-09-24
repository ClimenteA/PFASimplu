package incasari

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
	"github.com/ClimenteA/pfasimplu-go/types"
)

func getIncasariJsonPaths(user auth.Account) ([]string, error) {

	incasariMetadataJson := []string{}

	err := filepath.Walk(user.StocareIncasari,
		func(path string, _ os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if strings.Contains(path, "metadata.json") {
				incasariMetadataJson = append(incasariMetadataJson, path)
			}

			return nil
		})
	if err != nil {
		log.Panicln(err)
	}

	return incasariMetadataJson, err

}

func getIncasariExtraJsonPaths(user auth.Account) ([]string, error) {

	incasariMetadataJson := []string{}

	err := filepath.Walk(user.StocareIncasariExtra,
		func(path string, _ os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if strings.Contains(path, "metadata.json") {
				incasariMetadataJson = append(incasariMetadataJson, path)
			}

			return nil
		})
	if err != nil {
		log.Panicln(err)
	}

	return incasariMetadataJson, err

}

func getInvoiceMetadata(path string) types.FacturaPlusExtraIncasari {

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()
	byteValue, _ := ioutil.ReadAll(jsonFile)

	var data types.FacturaPlusExtraIncasari
	json.Unmarshal(byteValue, &data)

	return data
}

func getExtraIncasariMetadata(path string) types.FacturaPlusExtraIncasari {

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()
	byteValue, _ := ioutil.ReadAll(jsonFile)

	var data types.FacturaPlusExtraIncasari
	json.Unmarshal(byteValue, &data)

	return data
}

func getInvoicesDataSlice(incasariMetadataJson []string, anul string) []types.FacturaPlusExtraIncasari {

	invoices := []types.FacturaPlusExtraIncasari{}
	now := time.Now()

	for _, path := range incasariMetadataJson {

		invoice := getInvoiceMetadata(path)

		if invoice.SursaVenit == "" {
			invoice.SursaVenit = "Venit din activitati independente"
		}

		if invoice.TipTranzactie == "" {
			invoice.TipTranzactie = "BANCAR"
		}

		iterDate, _ := time.Parse(time.RFC3339, invoice.Data+"T00:00:00Z")

		isBeforeNow := iterDate.Before(now)
		sameMonthYear := iterDate.Year() == now.Year() && iterDate.Month() == now.Month()

		if isBeforeNow || sameMonthYear {

			if strings.HasPrefix(invoice.Data, anul) {
				invoices = append(invoices, invoice)
			}
		}

	}

	return invoices

}

func getIncasariExtraDataSlice(incasariMetadataJson []string, anul string) []types.FacturaPlusExtraIncasari {

	extraIncasari := []types.FacturaPlusExtraIncasari{}
	now := time.Now()

	for _, path := range incasariMetadataJson {

		invoice := getExtraIncasariMetadata(path)
		iterDate, _ := time.Parse(time.RFC3339, invoice.Data+"T00:00:00Z")

		isBeforeNow := iterDate.Before(now)
		sameMonthYear := iterDate.Year() == now.Year() && iterDate.Month() == now.Month()

		if isBeforeNow || sameMonthYear {

			if strings.HasPrefix(invoice.Data, anul) {
				extraIncasari = append(extraIncasari, invoice)
			}
		}

	}

	return extraIncasari

}

func AdunaIncasari(user auth.Account, anul string) []types.FacturaPlusExtraIncasari {

	incasariMetadataJson, err := getIncasariJsonPaths(user)
	if err != nil {
		panic(err)
	}

	incasariExtraMetadataJson, err := getIncasariExtraJsonPaths(user)
	if err != nil {
		panic(err)
	}

	invoices := getInvoicesDataSlice(incasariMetadataJson, anul)
	extraIncasari := getIncasariExtraDataSlice(incasariExtraMetadataJson, anul)

	invoices = append(invoices, extraIncasari...)

	sort.Slice(invoices, func(i, j int) bool {
		return invoices[i].Numar > invoices[j].Numar
	})

	return invoices
}
