package registre

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/tabelcsv"
	"github.com/ClimenteA/pfasimplu-go/utils"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
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
		aniInregistrati := utils.GetAniInregistrati(user)

		log.Println("Filtreaza datale pentru anul: ", filterYear, aniInregistrati)

		declaratii := AdunaDeclaratii(user, filterYear)
		incasari := AdunaIncasari(user, filterYear)
		cheltuieli := AdunaCheltuieli(user, filterYear)
		platiAnaf := CalculPlatiAnaf(declaratii)
		totalIncasariBrut := CalculeazaIncasariBrut(incasari)
		totalCheltuieliDeductibile := CalculeazaCheltuieliDeductibile(cheltuieli)
		totalIncasariNet := totalIncasariBrut - totalCheltuieliDeductibile - platiAnaf
		totalPlatiCatreStat := CalculeazaPlatiCatreStat(totalIncasariNet, platiAnaf, filterYear)
		profitAnual := CalculeazaProfitAnual(user, filterYear)
		profitAnualProcent := 0.0
		showProfitAnual := false
		if profitAnual > 0 {
			profitAnual = profitAnual - totalPlatiCatreStat
			profitAnualProcent = (profitAnual / totalIncasariBrut) * 100
			showProfitAnual = true
		}

		registruJurnal := CreeazaRegistruJurnal(incasari, cheltuieli)
		registruInventar := CreeazaRegistruInventar(cheltuieli)
		registruFiscal := CreeazaRegistruFiscal(aniInregistrati, incasari, cheltuieli, filterYear)

		tabelcsv.CreeazaIncasariCSV(user.Stocare, incasari)
		tabelcsv.CreeazaCheltuieliCSV(user.Stocare, cheltuieli)
		tabelcsv.CreeazaRegistruJurnalCSV(user.Stocare, registruJurnal)
		tabelcsv.CreeazaRegistruInventarCSV(user.Stocare, registruInventar)
		tabelcsv.CreeazaRegistruFiscalCSV(user.Stocare, registruFiscal)

		return c.Render("registre", fiber.Map{
			"AniInregistrati":            aniInregistrati,
			"Incasari":                   incasari,
			"Cheltuieli":                 cheltuieli,
			"ProfitAnual":                fmt.Sprintf("%.2f", profitAnual),
			"ProfitAnualProcent":         fmt.Sprintf("%.2f", profitAnualProcent),
			"ShowProfitAnual":            showProfitAnual,
			"Declaratii":                 declaratii,
			"RegistruJurnal":             registruJurnal,
			"RegistruInventar":           registruInventar,
			"RegistruFiscal":             registruFiscal,
			"TotalIncasariBrut":          fmt.Sprintf("%.2f", totalIncasariBrut),
			"TotalIncasariNet":           fmt.Sprintf("%.2f", totalIncasariNet),
			"TotalCheltuieliDeductibile": fmt.Sprintf("%.2f", totalCheltuieliDeductibile),
			"TotalPlatiCatreStat":        fmt.Sprintf("%.2f", totalPlatiCatreStat),
			"CaleIncasariCSV":            filepath.Join(user.Stocare, "incasari.csv"),
			"CaleCheltuieliCSV":          filepath.Join(user.Stocare, "cheltuieli.csv"),
			"CaleRegistruJurnalCSV":      filepath.Join(user.Stocare, "registru_jurnal.csv"),
			"CaleRegistruInventarCSV":    filepath.Join(user.Stocare, "registru_inventar.csv"),
			"CaleRegistruFiscalCSV":      filepath.Join(user.Stocare, "registru_fiscal.csv"),
		}, "base")
	})
}
