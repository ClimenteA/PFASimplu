package registre

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

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

		if declaratie.PlataAnaf != 0.0 && anul == strconv.Itoa(declaratie.PlataPtAnul) {
			declaratii = append(declaratii, declaratie)
			continue
		}

		if strings.HasPrefix(declaratie.Data, anul) && declaratie.PlataAnaf == 0.0 {
			declaratii = append(declaratii, declaratie)
		}

	}

	sort.Slice(declaratii, func(i, j int) bool {

		ti, err := time.Parse(time.RFC3339, declaratii[i].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		tj, err := time.Parse(time.RFC3339, declaratii[j].Data+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		return ti.After(tj)
	})

	return declaratii

}

func AdunaDeclaratii(user auth.Account, anul string) []declaratii.Declaratie {

	docMetadataJson, err := getDeclaratiiJsonPaths(user)
	if err != nil {
		panic(err)
	}

	declaratii := getDocsDataSlice(docMetadataJson, anul)

	return declaratii
}
