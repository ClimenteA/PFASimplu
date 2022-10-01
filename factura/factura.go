package factura

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleInvoicePage(app fiber.App, store session.Store) {
	handleInvoicePage(app, store)
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

func handleInvoicePage(app fiber.App, store session.Store) {

	app.Get("/factura", func(c *fiber.Ctx) error {

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
		ultimaSerie := "INV"
		ultimulNumar := 0
		if len(incasari) > 0 {
			ultimaSerie = incasari[0].Serie
			ultimulNumar = incasari[0].Numar
		}

		return c.Render("factura", fiber.Map{
			"Incasari":     incasari,
			"UltimaSerie":  ultimaSerie,
			"UltimulNumar": ultimulNumar + 1,
			"Anul":         filterYear,
		}, "base")

	})

}
