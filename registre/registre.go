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
	outputs "github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
	inputs "github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
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

func GetCurrentUser(currentUserPath string) auth.Account {

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
			err := os.RemoveAll(delPath)
			if err != nil {
				return c.Redirect("/registre-contabile?title=Calea catre fisier gresita&content=Fisierul dorit nu a fost gasit.")
			}
			delSplitPath, _ := filepath.Split(delPath)
			files, _ := ioutil.ReadDir(delSplitPath)

			if len(files) == 0 && !strings.HasSuffix(delSplitPath, "incasari/") {
				err := os.RemoveAll(delSplitPath)
				if err != nil {
					log.Panicln(err)
				}
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

		intYear := time.Now().Year()
		filterYear := strconv.Itoa(intYear)
		if r.Anul != "" {
			filterYear = r.Anul
		}

		user := GetCurrentUser(fmt.Sprint(currentUserPath))
		aniInregistrati := utils.GetAniInregistrati(user)

		declaratii := declaratii.AdunaDeclaratii(user, filterYear)
		incasari := inputs.AdunaIncasari(user, filterYear)
		cheltuieli := outputs.AdunaCheltuieli(user, filterYear)

		totalIncasariBrut := CalculeazaIncasariBrut(incasari)
		totalCheltuieliDeductibile := CalculeazaCheltuieliDeductibile(cheltuieli)
		totalIncasariNet := 0.0
		if totalIncasariBrut > 0 {
			totalIncasariNet = totalIncasariBrut - totalCheltuieliDeductibile
		}

		incasariPeLuni := inputs.AddIncasariPeLuni(incasari, filterYear)
		cheltuieliPeLuni := outputs.AddCheltuieliPeLuni(cheltuieli, filterYear)

		incasariRj := appendTotalLunarIncasari(incasari, incasariPeLuni, filterYear)
		cheltuieliRj := appendTotalLunarCheltuieli(cheltuieli, cheltuieliPeLuni, filterYear)
		registruJurnal := CreeazaRegistruJurnal(incasariRj, cheltuieliRj)

		registruFiscal := CreeazaRegistruFiscal(aniInregistrati, incasari, cheltuieli, filterYear)

		CaleIncasari := tabelcsv.CreeazaIncasariCSV(user.Stocare, filterYear, incasari)
		CaleCheltuieli := tabelcsv.CreeazaCheltuieliCSV(user.Stocare, filterYear, cheltuieli)
		CaleRegistruJurnal := tabelcsv.CreeazaRegistruJurnalCSV(user.Stocare, filterYear, registruJurnal)
		CaleRegistruFiscal := tabelcsv.CreeazaRegistruFiscalCSV(user.Stocare, filterYear, registruFiscal)

		registruInventar := CreeazaRegistruInventar(cheltuieli)
		tabelcsv.CreeazaRegistruInventarCSV(user.Stocare, filterYear+"_", registruInventar)
		registruInventar = tabelcsv.FullRegistruInventar(user.Stocare, filterYear)
		CaleRegistruInventar := tabelcsv.CreeazaRegistruInventarCSV(filepath.Join(user.Stocare, "inventar"), "", registruInventar)

		config := staticdata.LoadPFAConfig()

		plafonTVA := 300000.0
		for _, prag := range config.PlafonTVA {
			if strconv.Itoa(prag.An) == filterYear {
				plafonTVA = prag.Valoare
				break
			}
		}

		platitorTVA := false
		if totalIncasariBrut > plafonTVA {
			platitorTVA = true
		}

		platiCatreStatRounded, totalPlatiCatreStat, totalIncasariNet := GetPlatiCatreStatRounded(totalIncasariNet, filterYear, declaratii)
		intfilterYear, _ := strconv.Atoi(filterYear)
		months := 12.0
		VenitNetLunar := totalIncasariNet / months
		VenitBrutLunar := totalIncasariBrut / months
		if intfilterYear == intYear {
			partialMonths := float64(time.Now().Month() - 1)
			VenitNetLunar = totalIncasariNet / partialMonths
			VenitBrutLunar = totalIncasariBrut / partialMonths
			CheltuieliEstimate := (totalCheltuieliDeductibile / partialMonths) * months
			VenitEstimatNet := (VenitNetLunar * months) - CheltuieliEstimate
			platiCatreStatRounded, totalPlatiCatreStat, _ = GetPlatiCatreStatRounded(VenitEstimatNet, filterYear, declaratii)
		}

		return c.Render("registre", fiber.Map{
			"AniInregistrati":            aniInregistrati,
			"Incasari":                   incasari,
			"Cheltuieli":                 cheltuieli,
			"Declaratii":                 declaratii,
			"RegistruJurnal":             registruJurnal,
			"RegistruInventar":           registruInventar,
			"RegistruFiscal":             registruFiscal,
			"PlatitorTVA":                platitorTVA,
			"VenitNetLunar":              fmt.Sprintf("%.2f", VenitNetLunar),
			"VenitBrutLunar":             fmt.Sprintf("%.2f", VenitBrutLunar),
			"TotalIncasariBrut":          fmt.Sprintf("%.2f", totalIncasariBrut),
			"TotalIncasariNet":           fmt.Sprintf("%.2f", totalIncasariNet),
			"TotalCheltuieliDeductibile": fmt.Sprintf("%.2f", totalCheltuieliDeductibile),
			"TotalPlatiCatreStat":        fmt.Sprintf("%.2f", totalPlatiCatreStat),
			"CaleIncasariCSV":            CaleIncasari.CSV,
			"CaleCheltuieliCSV":          CaleCheltuieli.CSV,
			"CaleRegistruJurnalCSV":      CaleRegistruJurnal.CSV,
			"CaleRegistruInventarCSV":    CaleRegistruInventar.CSV,
			"CaleRegistruFiscalCSV":      CaleRegistruFiscal.CSV,
			"CaleIncasariXLSX":           CaleIncasari.XLSX,
			"CaleCheltuieliXLSX":         CaleCheltuieli.XLSX,
			"CaleRegistruJurnalXLSX":     CaleRegistruJurnal.XLSX,
			"CaleRegistruInventarXLSX":   CaleRegistruInventar.XLSX,
			"CaleRegistruFiscalXLSX":     CaleRegistruFiscal.XLSX,
			"IncasariPeLuni":             incasariPeLuni,
			"CheltuieliPeLuni":           cheltuieliPeLuni,
			"PlatiCatreStat":             platiCatreStatRounded,
		}, "base")
	})
}
