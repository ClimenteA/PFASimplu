package extrasbancar

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
)

func getDeclaratiiJsonPaths(user auth.Account) ([]string, error) {

	docMetadataJson := []string{}

	err := filepath.Walk(user.StocareDeclaratii,
		func(path string, _ os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if strings.Contains(path, "metadata.json") {
				docMetadataJson = append(docMetadataJson, path)
			}

			return nil
		})
	if err != nil {
		log.Println(err)
	}

	return docMetadataJson, err

}

func getDocMetadata(path string) declaratii.Declaratie {

	var data declaratii.Declaratie

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func getDocsDataSlice(docMetadataJson []string, anul string) []declaratii.Declaratie {

	declaratii := []declaratii.Declaratie{}

	for _, path := range docMetadataJson {

		declaratie := getDocMetadata(path)

		if declaratie.TipDocument == "Extras bancar ING" && strings.HasPrefix(declaratie.Data, anul) {
			declaratii = append(declaratii, declaratie)
		}

	}

	return declaratii

}

func AdunaExtraseING(user auth.Account, anul string) []declaratii.Declaratie {

	docMetadataJson, err := getDeclaratiiJsonPaths(user)
	if err != nil {
		panic(err)
	}

	extraseIngMetadata := getDocsDataSlice(docMetadataJson, anul)

	return extraseIngMetadata
}
