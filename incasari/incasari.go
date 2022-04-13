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

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleIncasari(app fiber.App, store session.Store) {
	handleIncasari(app, store)
}

type Account struct {
	Email   string `json:"email"`
	Parola  string `json:"parola"`
	Stocare string `json:"stocare"`
}

type Factura struct {
	Serie        string  `json:"serie"`
	Numar        int     `json:"numar"`
	Data         string  `json:"data"`
	SumaIncasata float64 `json:"suma_incasata"`
}

func getInvoiceJsonPath(dirName string) string {

	dirPath := filepath.Join("facturi", dirName)

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, dirName, dirName+".json")
	} else {
		os.MkdirAll(dirPath, 0750)
		return filepath.Join(dirPath, dirName, dirName+".json")
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
	_ = ioutil.WriteFile(filePath, file, 0644)
}

func getCurrentUser(currentUserPath string) Account {

	var data Account

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

			dirName := filepath.Join(user.Stocare, data+"-"+serie+"-"+strconv.Itoa(numar))

			invoiceData := Factura{
				Serie:        serie,
				Numar:        numar,
				Data:         data,
				SumaIncasata: suma_incasata,
			}

			invoiceJsonPath := getInvoiceJsonPath(dirName)
			setInvoiceData(invoiceData, invoiceJsonPath)

			invoicePath := getInvoicePath(dirName)
			c.SaveFile(fisier, filepath.Join(invoicePath, fisier.Filename))

			log.Println(dirName)
			log.Println(fisier.Filename)
			log.Println(invoiceData)
			log.Println(data)

		}

		return c.Redirect("/adauga-incasari")

	})

}
