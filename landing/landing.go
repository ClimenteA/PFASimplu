package landing

import (
	"io/ioutil"
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleLandingPage(app fiber.App, store session.Store) {
	handleLandingPage(app, store)
}

func handleLandingPage(app fiber.App, store session.Store) {

	app.Get("/landing", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		userLoggedIn := true
		if currentUserPath == nil {
			userLoggedIn = false
		}

		content, err := ioutil.ReadFile("./assets/public/README.md")
		if err != nil {
			log.Fatal(err)
		}

		readme := string(content)

		return c.Render("landing", fiber.Map{
			"UserLoggedIn": userLoggedIn,
			"Readme":       readme,
		})
	})

}
