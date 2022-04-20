package registre

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

type Filepath struct {
	Path string `query:"path"`
}

type ReportYear struct {
	Anul string `query:"anul"`
}

func HandleRegistre(app fiber.App, store session.Store) {
	handleRegistre(app, store)
}

func getDocJsonPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, "metadata.json")
	} else {
		os.MkdirAll(dirPath, 0750)
		return filepath.Join(dirPath, "metadata.json")
	}
}

func getDocPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return dirPath
	} else {
		os.MkdirAll(dirPath, 0750)
		return dirPath
	}

}

func setDocData(docData declaratii.Declaratie, filePath string) {
	file, _ := json.MarshalIndent(docData, "", " ")
	err := ioutil.WriteFile(filePath, file, 0644)
	if err != nil {
		panic(err)
	}
}

func getCurrentUser(currentUserPath string) auth.Account {

	var data auth.Account

	jsonFile, err := os.Open(currentUserPath)
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func handleRegistre(app fiber.App, store session.Store) {

	app.Get("/download-fisier", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		f := new(Filepath)

		if err := c.QueryParser(f); err != nil {
			return c.Redirect("/registre-contabile?title=Calea catre fisier gresita&content=Fisierul dorit nu a fost gasit.")
		}

		return c.Download(f.Path)

	})

	app.Get("/sterge-fisier", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		f := new(Filepath)

		if err := c.QueryParser(f); err != nil {
			return c.Redirect("/registre-contabile?title=Calea catre fisier gresita&content=Fisierul dorit nu a fost gasit.")
		}

		if _, err := os.Stat(f.Path); err == nil || os.IsExist(err) {

			delPath := filepath.Dir(f.Path)

			if strings.Contains(f.Path, "cheltuieli") || strings.Contains(f.Path, "declaratii") {
				delPath, _ = filepath.Split(delPath)
			}

			err := os.RemoveAll(delPath)
			if err != nil {
				return c.Redirect("/registre-contabile?title=Calea catre fisier gresita&content=Fisierul dorit nu a fost gasit.")
			}

		} else {
			return c.Redirect("/registre-contabile?title=Calea catre fisier gresita&content=Fisierul dorit nu a fost gasit.")
		}

		return c.Redirect("/registre-contabile?title=Fisierul sters&content=Fisierul dorit a fost sters.")

	})

	app.Get("/registre-contabile", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		r := new(ReportYear)

		if err := c.QueryParser(r); err != nil {
			return c.Redirect("/registre-contabile?title=Anul fara date&content=Nu au fost gasite date pentru anul cerut.")
		}

		filterYear := strconv.Itoa(time.Now().Year())
		if r.Anul != "" {
			filterYear = r.Anul
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		log.Println("Filtreaza datale pentru anul: ", filterYear, reflect.TypeOf(filterYear))

		incasari := AdunaIncasari(user, filterYear)
		cheltuieli := AdunaCheltuieli(user, filterYear)
		declaratii := AdunaDeclaratii(user, filterYear)
		totalIncasariBrut := CalculeazaIncasariBrut(incasari)
		totalCheltuieliDeductibile := CalculeazaCheltuieliDeductibile(cheltuieli)
		totalIncasariNet := totalIncasariBrut - totalCheltuieliDeductibile
		totalPlatiCatreStat := CalculeazaPlatiCatreStat(totalIncasariNet, filterYear)

		return c.Render("registre", fiber.Map{
			"Incasari":                   incasari,
			"Cheltuieli":                 cheltuieli,
			"Declaratii":                 declaratii,
			"TotalIncasariBrut":          totalIncasariBrut,
			"TotalIncasariNet":           totalIncasariNet,
			"TotalCheltuieliDeductibile": totalCheltuieliDeductibile,
			"TotalPlatiCatreStat":        totalPlatiCatreStat,
		}, "base")
	})

	app.Post("/registre-contabile", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		if form, err := c.MultipartForm(); err == nil {

			tip_document := form.Value["tip_document"][0]
			data := form.Value["data"][0]

			fisier, err := c.FormFile("fisier")
			if err != nil {
				panic(err)
			}

			uid := shortuuid.New()
			dirName := filepath.Join(user.Stocare, "registre", data, uid)

			docData := declaratii.Declaratie{
				Data:        data,
				TipDocument: tip_document,
			}

			docJsonPath := getDocJsonPath(dirName)
			setDocData(docData, docJsonPath)

			docPath := getDocPath(dirName)
			c.SaveFile(fisier, filepath.Join(docPath, fisier.Filename))

		}

		return c.Redirect("/registre-contabile")

	})

}
