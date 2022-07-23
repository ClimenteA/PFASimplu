package download

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

type DeclaratieAn struct {
	Anul string `query:"anul"`
}

func HandleDownloadDateCont(app fiber.App, store session.Store) {
	downloadDateCont(app, store)
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

func downloadDateCont(app fiber.App, store session.Store) {

	app.Get("/download-date-cont", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))
		aniInregistrati := utils.GetAniInregistrati(user)

		return c.Render("downloadcont", fiber.Map{
			"AniInregistrati": aniInregistrati,
		}, "base")

	})

	app.Post("/download-date-cont", func(c *fiber.Ctx) error {

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

			anul := form.Value["anul"][0]
			fmt.Println(anul)

			zipPath := user.Stocare + ".zip"
			utils.ZipDir(user.Stocare, zipPath)

			return c.Download(zipPath)
		}

		return c.Redirect("/download-date-cont?title=Date adunate&content=Datele au fost adunate intr-un zip.")

	})

}
