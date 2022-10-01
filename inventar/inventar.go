package inventar

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	outputs "github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/registre"
	"github.com/ClimenteA/pfasimplu-go/tabelcsv"
	"github.com/ClimenteA/pfasimplu-go/types"
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

func HandleInventarPage(app fiber.App, store session.Store) {
	handleInventarPage(app, store)
}

func handleInventarPage(app fiber.App, store session.Store) {

	app.Get("/scoate-din-inventar", func(c *fiber.Ctx) error {

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
		cheltuieli := outputs.AdunaCheltuieli(user, filterYear)
		registruInventar := registre.CreeazaRegistruInventar(cheltuieli)
		tabelcsv.CreeazaRegistruInventarCSV(user.Stocare, filterYear+"_", registruInventar)
		registruInventar = tabelcsv.FullRegistruInventar(user.Stocare, filterYear)
		registruInventarCSVPath := tabelcsv.CreeazaRegistruInventarCSV(filepath.Join(user.Stocare, "inventar"), "", registruInventar)

		return c.Render("scoate_din_inventar", fiber.Map{
			"RegistruInventar":        registruInventar,
			"CaleRegistruInventarCSV": registruInventarCSVPath,
		}, "base")
	})

	app.Post("/scoate-din-inventar", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		fisier, err := c.FormFile("fisier")
		if err != nil {
			panic(err)
		}

		if form, err := c.MultipartForm(); err == nil {

			cale_obiect_mijloc_fix := form.Value["cale_obiect_mijloc_fix"][0]
			data := form.Value["data"][0]
			tip_operatiune := form.Value["tip_operatiune"][0]

			cale_cheltuiala_root, _ := filepath.Split(cale_obiect_mijloc_fix)
			cale_metadata := filepath.Join(cale_cheltuiala_root, "metadata.json")

			cheltuiala := outputs.GetExpenseMetadata(cale_metadata)

			cale_dovada_scos_din_uz := filepath.Join(cale_cheltuiala_root, "Dovada scoatere din uz - "+fisier.Filename)
			if _, err := os.Stat(cale_dovada_scos_din_uz); err == nil {
				os.Remove(cale_dovada_scos_din_uz)
			}
			c.SaveFile(fisier, cale_dovada_scos_din_uz)

			cheltuiala.ScosDinUz = true
			cheltuiala.DetaliiIesireDinUz = types.IesireDinUz{
				ScosDinUz:             true,
				DataIesireDinUz:       data,
				CaleDovadaIesireDinUz: cale_dovada_scos_din_uz,
				ModalidateIesireDinUz: tip_operatiune,
			}

			outputs.SetExpenseData(cheltuiala, cale_metadata)

		}

		return c.Redirect("/scoate-din-inventar?title=Scos din uz&content=Obiect/Mijloc fix scos din uz. Vezi registre contabile.")

	})

}
