package tabelpdf

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

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

func HandleTabelPDFPage(app fiber.App, store session.Store) {
	handleTabelPdfage(app, store)
}

func handleTabelPdfage(app fiber.App, store session.Store) {

	app.Get("/tabel-incasari-pdf", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := GetCurrentUser(fmt.Sprint(currentUserPath))
		filterYear := strconv.Itoa(time.Now().Year())
		incasari := incasari.AdunaIncasari(user, filterYear)

		return c.Render("tabel_pdf_incasari", fiber.Map{
			"Incasari": incasari,
			"Anul":     filterYear,
		})

	})

	app.Get("/tabel-cheltuieli-pdf", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := GetCurrentUser(fmt.Sprint(currentUserPath))
		filterYear := strconv.Itoa(time.Now().Year())
		cheltuieli := cheltuieli.AdunaCheltuieli(user, filterYear)

		return c.Render("tabel_pdf_cheltuieli", fiber.Map{
			"Cheltuieli": cheltuieli,
			"Anul":       filterYear,
		})

	})

}
