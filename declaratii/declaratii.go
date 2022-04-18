package declaratii

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

func HandleDeclaratii(app fiber.App, store session.Store) {
	handleDeclaratii(app, store)
}

type Declaratie struct {
	Data         string `json:"data"`
	TipDocument  string `json:"tip_document"`
	CaleDocument string `json:"cale_document"`
}

func getDocJsonPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, "metadata.json")
	} else {
		os.MkdirAll(dirPath, 0750)
		return filepath.Join(dirPath, "metadata.json")
	}
}

func getDocPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return dirPath
	} else {
		os.MkdirAll(dirPath, 0750)
		return dirPath
	}

}

func setDocData(docData Declaratie, filePath string) {
	file, _ := json.MarshalIndent(docData, "", " ")
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

func handleDeclaratii(app fiber.App, store session.Store) {

	app.Get("/adauga-declaratii", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		if sess.Get("currentUser") == nil {
			return c.Redirect("/login")
		}

		return c.Render("declaratii", fiber.Map{}, "base")
	})

	app.Post("/adauga-declaratii", func(c *fiber.Ctx) error {

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

			tip_document := form.Value["tip_document"][0]
			data := form.Value["data"][0]

			fisier, err := c.FormFile("fisier")
			if err != nil {
				panic(err)
			}

			uid := shortuuid.New()
			dirName := filepath.Join(user.StocareDeclaratii, data, uid)

			docPath := getDocPath(dirName)
			caleDocument := filepath.Join(docPath, fisier.Filename)
			c.SaveFile(fisier, caleDocument)

			docData := Declaratie{
				Data:         data,
				TipDocument:  tip_document,
				CaleDocument: caleDocument,
			}

			docJsonPath := getDocJsonPath(dirName)
			setDocData(docData, docJsonPath)

		}

		return c.Redirect("/adauga-declaratii")

	})

}
