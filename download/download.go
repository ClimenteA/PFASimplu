package download

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

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

			zipSrcPath := filepath.Join(user.Stocare, "ZIP")
			zipDstPath := filepath.Join(user.Stocare, anul+".zip")

			errsrc := os.RemoveAll(zipSrcPath)
			if errsrc != nil {
				fmt.Println("No source SRC ZIP folder found")
			}

			errdst := os.RemoveAll(zipDstPath)
			if errdst != nil {
				fmt.Println("No source DST ZIP folder found")
			}

			allRequestedDirs := utils.GetAllDirsForYear(anul, user)

			for _, fp := range allRequestedDirs {

				bytesRead, err := ioutil.ReadFile(fp)
				if err != nil {
					log.Fatal(err)
				}

				srcFilePath := filepath.Join(zipSrcPath, fp)
				srcPath := filepath.Dir(srcFilePath)

				os.MkdirAll(srcPath, 0755)

				err = ioutil.WriteFile(srcFilePath, bytesRead, 0755)
				if err != nil {
					log.Fatal(err)
				}
			}

			utils.ZipDir(zipSrcPath, zipDstPath)

			errsrcafter := os.RemoveAll(zipSrcPath)
			if errsrcafter != nil {
				fmt.Println("No source SRC ZIP folder found")
			}

			return c.Download(zipDstPath)

		}

		return c.Redirect("/download-date-cont?title=Eroare&content=Arhiva nu a putut fi creata.")

	})

}
