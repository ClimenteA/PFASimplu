package updates

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"
	"os"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleUpdatesPage(app fiber.App, store session.Store) {
	handleUpdatesPage(app, store)
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

func handleUpdatesPage(app fiber.App, store session.Store) {

	app.Get("/actualizare-aplicatie", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		config := staticdata.LoadPFAConfig()

		var latestPfaConfig staticdata.Config

		pfaConfigUrl := "https://raw.githubusercontent.com/ClimenteA/PFASimplu/main/assets/public/pfaconfig.json"
		resp, err := http.Get(pfaConfigUrl)
		if err != nil {
			log.Panicln("URL " + pfaConfigUrl + " nu mai este valabil. Descarca aplicatia manual din github releases.")
		}
		defer resp.Body.Close()
		byteValue, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Panicln("URL " + pfaConfigUrl + " nu mai este valabil. Descarca aplicatia manual din github releases.")
		}
		json.Unmarshal(byteValue, &latestPfaConfig)

		updateNeeded := false
		if config.VersiuneAplicatie != latestPfaConfig.VersiuneAplicatie {
			updateNeeded = true
		}

		versionColor := "text-nok"
		if updateNeeded {
			versionColor = "text-nok"
		}

		return c.Render("update_app", fiber.Map{
			"VersiuneAplicatie":       config.VersiuneAplicatie,
			"UltimaVersiuneAplicatie": latestPfaConfig.VersiuneAplicatie,
			"UpdateNeeded":            updateNeeded,
			"VersionColor":            versionColor,
		}, "base")

	})

}
