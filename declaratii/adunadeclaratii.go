package declaratii

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

func getDocMetadata(path string) Declaratie {

	var data Declaratie

	jsonFile, err := os.Open(path)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func getDocsDataSlice(docMetadataJson []string, anul string) []Declaratie {

	declaratii := []Declaratie{}
	now := time.Now()

	for _, path := range docMetadataJson {

		declaratie := getDocMetadata(path)

		if declaratie.TipDocument == "Declaratie unica (212)" || declaratie.TipDocument == "Dovada plata impozite" || declaratie.TipDocument == "Dovada incarcare Declaratie 212" {
			if anul == strconv.Itoa(declaratie.PtAnul) {
				declaratii = append(declaratii, declaratie)
			}
			continue
		}

		iterDate, _ := time.Parse(time.RFC3339, declaratie.Data+"T00:00:00Z")
		sameMonthYear := iterDate.Year() == now.Year() && iterDate.Month() == now.Month()

		if iterDate.Before(now) || sameMonthYear {
			if strings.HasPrefix(declaratie.Data, anul) {
				declaratii = append(declaratii, declaratie)
			}
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

func AdunaDeclaratii(user auth.Account, anul string) []Declaratie {

	docMetadataJson, err := getDeclaratiiJsonPaths(user)
	if err != nil {
		panic(err)
	}

	declaratii := getDocsDataSlice(docMetadataJson, anul)

	return declaratii
}
