package incasariextra

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

func HandleIncasariExtra(app fiber.App, store session.Store) {
	handleIncasariExtra(app, store)
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

func GetIncasareExtraPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return dirPath
	} else {
		os.MkdirAll(dirPath, 0750)
		return dirPath
	}

}

func SetIncasareExtraData(data types.ExtraIncasare, filePath string) {
	file, _ := json.MarshalIndent(data, "", " ")
	err := ioutil.WriteFile(filePath, file, 0644)
	if err != nil {
		panic(err)
	}
}

func handleIncasariExtra(app fiber.App, store session.Store) {

	app.Get("/adauga-incasari-extra", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		return c.Render("incasari_extra", fiber.Map{}, "base")
	})

	app.Post("/adauga-incasari-extra", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		if form, err := c.MultipartForm(); err == nil {
			tip_tranzactie := form.Value["tip_tranzactie"][0]
			data := form.Value["data"][0]
			sursa_venit := form.Value["sursa_venit"][0]

			suma_incasata, err := strconv.ParseFloat(form.Value["suma_incasata"][0], 64)
			if err != nil {
				panic(err)
			}

			fisier, err := c.FormFile("fisier")
			if err != nil {
				panic(err)
			}

			uid := shortuuid.New()
			user := getCurrentUser(fmt.Sprint(currentUserPath))
			dirName := filepath.Join(user.StocareCheltuieli, data, uid)
			incasarePath := GetIncasareExtraPath(dirName)
			caleIncasare := filepath.Join(incasarePath, fisier.Filename)

			incasareExtra := types.ExtraIncasare{
				SursaVenit:    sursa_venit,
				Data:          data,
				TipTranzactie: tip_tranzactie,
				SumaIncasata:  suma_incasata,
				CaleIncasare:  caleIncasare,
			}

			SetIncasareExtraData(incasareExtra, caleIncasare)
			c.SaveFile(fisier, caleIncasare)
			go utils.SmallerImg(caleIncasare)

		}

		return c.Redirect("/adauga-incasari-extra?title=Incasare adaugata&content=Incasarea a fost adaugata. Vezi registre contabile.")

	})

}
