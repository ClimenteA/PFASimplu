package registre

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/incasari"
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
		log.Println(err)
	}

	return incasariMetadataJson, err

}

func getInvoiceMetadata(path string) incasari.Factura {

	var data incasari.Factura

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func getInvoicesDataSlice(incasariMetadataJson []string, anul string) []incasari.Factura {

	invoices := []incasari.Factura{}

	for _, path := range incasariMetadataJson {

		invoice := getInvoiceMetadata(path)

		if strings.HasPrefix(invoice.Data, anul) {
			invoices = append(invoices, invoice)
		}
	}

	sort.Slice(invoices, func(i, j int) bool {
		return invoices[i].Numar > invoices[j].Numar
	})

	return invoices

}

func AdunaIncasari(user auth.Account, anul string) []incasari.Factura {

	incasariMetadataJson, err := getIncasariJsonPaths(user)
	if err != nil {
		panic(err)
	}

	invoices := getInvoicesDataSlice(incasariMetadataJson, anul)

	return invoices
}
