package utils

import (
	"io/ioutil"
	"log"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

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

func GetAllDirs(user auth.Account) []string {

	allDirs := []string{}

	incasariDirs := getDirs(user.StocareIncasari)
	incasariExtraDirs := getDirs(user.StocareIncasariExtra)
	cheltuieliDirs := getDirs(user.StocareCheltuieli)
	declaratiiDirs := getDirs(user.StocareDeclaratii)

	allDirs = append(allDirs, incasariDirs...)
	allDirs = append(allDirs, incasariExtraDirs...)
	allDirs = append(allDirs, cheltuieliDirs...)
	allDirs = append(allDirs, declaratiiDirs...)

	return allDirs

}

func GetAllStocareFiles(filterYear string, user auth.Account) []string {

	files, err := ioutil.ReadDir(user.Stocare)
	if err != nil {
		log.Fatal(err)
	}

	allFiles := []string{}
	for _, file := range files {
		if !file.IsDir() {
			year := strings.Split(file.Name(), "_")[0]
			if filterYear == year {
				allFiles = append(allFiles, filepath.Join(user.Stocare, file.Name()))
			}
		}
	}

	return allFiles

}

func GetAllIncasariFiles(filterYear string, user auth.Account) []string {

	dirs, err := ioutil.ReadDir(user.StocareIncasari)
	if err != nil {
		log.Fatal(err)
	}

	allFiles := []string{}
	for _, dir := range dirs {
		if dir.IsDir() {
			year := strings.Split(dir.Name(), "-")[0]
			if filterYear == year {
				path := filepath.Join(user.StocareIncasari, dir.Name())
				files, err := ioutil.ReadDir(path)
				if err != nil {
					log.Fatal(err)
				}
				for _, file := range files {
					allFiles = append(allFiles, filepath.Join(path, file.Name()))
				}
			}
		}
	}

	return allFiles

}

func GetAllIncasariExtraFiles(filterYear string, user auth.Account) []string {

	dirs, err := ioutil.ReadDir(user.StocareIncasariExtra)
	if err != nil {
		log.Fatal(err)
	}

	allFiles := []string{}
	for _, dir := range dirs {
		if dir.IsDir() {
			year := strings.Split(dir.Name(), "-")[0]
			if filterYear == year {
				path := filepath.Join(user.StocareIncasariExtra, dir.Name())
				subDirs, err := ioutil.ReadDir(path)
				if err != nil {
					log.Fatal(err)
				}

				for _, sdir := range subDirs {

					if sdir.IsDir() {
						sdirPath := filepath.Join(path, sdir.Name())
						files, err := ioutil.ReadDir(sdirPath)
						if err != nil {
							log.Fatal(err)
						}

						for _, file := range files {
							allFiles = append(allFiles, filepath.Join(sdirPath, file.Name()))
						}
					}
				}

			}
		}
	}

	return allFiles

}

func GetAllCheltuieliFiles(filterYear string, user auth.Account) []string {

	dirs, err := ioutil.ReadDir(user.StocareCheltuieli)
	if err != nil {
		log.Fatal(err)
	}

	allFiles := []string{}
	for _, dir := range dirs {
		if dir.IsDir() {
			year := strings.Split(dir.Name(), "-")[0]
			if filterYear == year {
				path := filepath.Join(user.StocareCheltuieli, dir.Name())
				subDirs, err := ioutil.ReadDir(path)
				if err != nil {
					log.Fatal(err)
				}

				for _, sdir := range subDirs {

					if sdir.IsDir() {
						sdirPath := filepath.Join(path, sdir.Name())
						files, err := ioutil.ReadDir(sdirPath)
						if err != nil {
							log.Fatal(err)
						}

						for _, file := range files {
							allFiles = append(allFiles, filepath.Join(sdirPath, file.Name()))
						}
					}
				}

			}
		}
	}

	return allFiles

}

func GetAllDeclaratiiFiles(filterYear string, user auth.Account) []string {

	dirs, err := ioutil.ReadDir(user.StocareDeclaratii)
	if err != nil {
		log.Fatal(err)
	}

	allFiles := []string{}
	for _, dir := range dirs {
		if dir.IsDir() {
			year := strings.Split(dir.Name(), "-")[0]
			if filterYear == year {
				path := filepath.Join(user.StocareDeclaratii, dir.Name())
				subDirs, err := ioutil.ReadDir(path)
				if err != nil {
					log.Fatal(err)
				}

				for _, sdir := range subDirs {

					if sdir.IsDir() {
						sdirPath := filepath.Join(path, sdir.Name())
						files, err := ioutil.ReadDir(sdirPath)
						if err != nil {
							log.Fatal(err)
						}

						for _, file := range files {
							allFiles = append(allFiles, filepath.Join(sdirPath, file.Name()))
						}
					}
				}

			}
		}
	}

	return allFiles

}

func GetAllDirsForYear(filterYear string, user auth.Account) []string {

	allFiles := []string{}

	stocareFiles := GetAllStocareFiles(filterYear, user)
	incasariFiles := GetAllIncasariFiles(filterYear, user)
	incasariExtraFiles := GetAllIncasariExtraFiles(filterYear, user)
	cheltuieliFiles := GetAllCheltuieliFiles(filterYear, user)
	declaratiiFiles := GetAllDeclaratiiFiles(filterYear, user)

	allFiles = append(allFiles, stocareFiles...)
	allFiles = append(allFiles, incasariFiles...)
	allFiles = append(allFiles, incasariExtraFiles...)
	allFiles = append(allFiles, cheltuieliFiles...)
	allFiles = append(allFiles, declaratiiFiles...)

	return allFiles

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

	allDirs := GetAllDirs(user)
	yearsUnique := []string{}
	for _, dirName := range allDirs {
		year := strings.Split(dirName, "-")[0]
		if !SliceContains(yearsUnique, year) {
			yearsUnique = append(yearsUnique, year)
		}
	}

	currentYear, _, _ := time.Now().Date()
	currentYearStr := strconv.Itoa(currentYear)
	if !SliceContains(yearsUnique, currentYearStr) {
		yearsUnique = append(yearsUnique, currentYearStr)
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
