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
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleIncasari(app fiber.App, store session.Store) {
	handleIncasari(app, store)
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

func setInvoiceData(invoiceData types.Factura, filePath string) {
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

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))
		filterYear := strconv.Itoa(time.Now().Year())

		incasari := AdunaIncasari(user, filterYear)
		ultimaSerie := "INV"
		ultimulNumar := 0
		if len(incasari) > 0 {
			ultimaSerie = incasari[0].Serie
			ultimulNumar = incasari[0].Numar
		}

		return c.Render("incasari", fiber.Map{
			"Incasari":     incasari,
			"UltimaSerie":  ultimaSerie,
			"UltimulNumar": ultimulNumar + 1,
			"Anul":         filterYear,
		}, "base")
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

			invoiceData := types.Factura{
				Serie:         serie,
				Numar:         numar,
				Data:          data,
				TipTranzactie: tip_tranzactie,
				SumaIncasata:  suma_incasata,
				CaleFactura:   caleFactura,
			}

			setInvoiceData(invoiceData, invoiceJsonPath)
			c.SaveFile(fisier, caleFactura)
			go utils.SmallerImg(caleFactura)

		}

		return c.Redirect("/adauga-incasari?title=Incasare adaugata&content=Incasarea a fost adaugata. Vezi registre contabile.")

	})

}
