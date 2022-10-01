package declaratieanaf

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

type DeclaratieAn struct {
	Anul string `query:"anul"`
}

func HandleDeclaratie212(app fiber.App, store session.Store) {
	handleDeclaratie(app, store)
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

func handleDeclaratie(app fiber.App, store session.Store) {

	app.Get("/declaratie-anaf", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		r := new(DeclaratieAn)

		if err := c.QueryParser(r); err != nil {
			return c.Redirect("/declaratie-anaf?title=Anul fara date&content=Nu au fost gasite date pentru anul cerut.")
		}

		filterYear := strconv.Itoa(time.Now().Year())
		if r.Anul != "" {
			filterYear = r.Anul
		}

		user := GetCurrentUser(fmt.Sprint(currentUserPath))
		yearsRegisterd := utils.GetAniInregistrati(user)

		log.Println("filterYear", filterYear)

		return c.Render("declaratie212", fiber.Map{
			"AniInregistrati": yearsRegisterd,
		}, "base")
	})

}
