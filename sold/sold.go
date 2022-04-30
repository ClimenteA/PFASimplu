package sold

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleSoldIntermediar(app fiber.App, store session.Store) {
	handleSold(app, store)
}

type SoldIntermediar struct {
	Sold float64 `json:"sold"`
	Anul int     `json:"anul"`
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

func setData(dataSold SoldIntermediar, filePath string) {
	file, _ := json.MarshalIndent(dataSold, "", " ")
	err := ioutil.WriteFile(filePath, file, 0644)
	if err != nil {
		panic(err)
	}
}

func handleSold(app fiber.App, store session.Store) {

	app.Get("/adauga-sold-intermediar", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))
		yearsRegisterd := utils.GetAniInregistrati(user)

		return c.Render("sold", fiber.Map{
			"AniInregistrati": yearsRegisterd,
		}, "base")
	})

	app.Post("/adauga-sold-intermediar", func(c *fiber.Ctx) error {

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

			sold_intermediar := form.Value["sold_intermediar"][0]
			anul := form.Value["anul"][0]

			sold, err := strconv.ParseFloat(sold_intermediar, 64)

			if err != nil {
				return c.Redirect("/adauga-sold-intermediar?title=Sold gresit&content=Soldul introdus nu este un numar")
			}

			anulInt, _ := strconv.Atoi(anul)

			dataSold := SoldIntermediar{
				Sold: sold,
				Anul: anulInt,
			}

			setData(dataSold, filepath.Join(user.Stocare, anul+"_sold.json"))

		}

		return c.Redirect("/adauga-sold-intermediar?title=Sold Intermediar&content=Sold intermediar adaugat. Vezi registre contabile.")

	})

}
