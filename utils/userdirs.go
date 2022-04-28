package utils

import (
	"io/ioutil"
	"log"
	"sort"
	"strconv"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
)

func getDirs(path string) []string {

	files, err := ioutil.ReadDir(path)
	if err != nil {
		log.Fatal(err)
	}

	dirs := []string{}
	for _, file := range files {
		if file.IsDir() {
			dirs = append(dirs, file.Name())
		}
	}

	return dirs

}

func getAllDirs(user auth.Account) []string {

	allDirs := []string{}

	incasariDirs := getDirs(user.StocareIncasari)
	cheltuieliDirs := getDirs(user.StocareCheltuieli)
	declaratiiDirs := getDirs(user.StocareDeclaratii)

	allDirs = append(allDirs, incasariDirs...)
	allDirs = append(allDirs, cheltuieliDirs...)
	allDirs = append(allDirs, declaratiiDirs...)

	return allDirs

}

func SliceContains(s []string, e string) bool {
	for _, a := range s {
		if a == e {
			return true
		}
	}
	return false
}

func GetAniInregistrati(user auth.Account) []string {

	allDirs := getAllDirs(user)
	yearsUnique := []string{}
	for _, dirName := range allDirs {
		year := strings.Split(dirName, "-")[0]
		if !SliceContains(yearsUnique, year) {
			yearsUnique = append(yearsUnique, year)
		}
	}

	sort.Slice(yearsUnique, func(i, j int) bool {

		yi, err := strconv.Atoi(yearsUnique[i])
		if err != nil {
			log.Fatal(yi)
		}

		yj, err := strconv.Atoi(yearsUnique[j])
		if err != nil {
			log.Fatal(yj)
		}

		return yi > yj
	})

	return yearsUnique

}
