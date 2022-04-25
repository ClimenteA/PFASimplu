package incasari

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

// TODO
// - la post salveaza ultima incasare in json in folderul incasari
// - la get ia ultima serie si numar din folderul incasari

func HandleIncasari(app fiber.App, store session.Store) {
	handleIncasari(app, store)
}

type Factura struct {
	Serie         string  `json:"serie"`
	Numar         int     `json:"numar"`
	Data          string  `json:"data"`
	TipTranzactie string  `json:"tip_tranzactie"`
	SumaIncasata  float64 `json:"suma_incasata"`
	CaleFactura   string  `json:"cale_factura"`
}

func getInvoiceJsonPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, "metadata.json")
	} else {
		os.MkdirAll(dirPath, 0750)
		return filepath.Join(dirPath, "metadata.json")
	}
}

func getInvoicePath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return dirPath
	} else {
		os.MkdirAll(dirPath, 0750)
		return dirPath
	}

}

func setInvoiceData(invoiceData Factura, filePath string) {
	file, _ := json.MarshalIndent(invoiceData, "", " ")
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

func handleIncasari(app fiber.App, store session.Store) {

	app.Get("/adauga-incasari", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		if sess.Get("currentUser") == nil {
			return c.Redirect("/login")
		}

		return c.Render("incasari", fiber.Map{}, "base")
	})

	app.Post("/adauga-incasari", func(c *fiber.Ctx) error {

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

			tip_tranzactie := form.Value["tip_tranzactie"][0]

			serie := strings.ToUpper(form.Value["serie"][0])
			data := form.Value["data"][0]

			fisier, err := c.FormFile("fisier")
			if err != nil {
				panic(err)
			}

			numar, err := strconv.Atoi(form.Value["numar"][0])
			if err != nil {
				panic(err)
			}

			suma_incasata, err := strconv.ParseFloat(form.Value["suma_incasata"][0], 64)
			if err != nil {
				panic(err)
			}

			dirName := filepath.Join(user.StocareIncasari, data+"-"+serie+"-"+strconv.Itoa(numar))
			invoicePath := getInvoicePath(dirName)
			invoiceJsonPath := getInvoiceJsonPath(dirName)
			caleFactura := filepath.Join(invoicePath, fisier.Filename)

			invoiceData := Factura{
				Serie:         serie,
				Numar:         numar,
				Data:          data,
				TipTranzactie: tip_tranzactie,
				SumaIncasata:  suma_incasata,
				CaleFactura:   caleFactura,
			}

			setInvoiceData(invoiceData, invoiceJsonPath)
			c.SaveFile(fisier, caleFactura)

		}

		return c.Redirect("/adauga-incasari")

	})

}