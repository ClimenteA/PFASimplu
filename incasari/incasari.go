package incasari

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleIncasari(app fiber.App, store session.Store) {
	handleIncasari(app, store)
}

func handleIncasari(app fiber.App, store session.Store) {

	app.Get("/adauga-incasari", func(c *fiber.Ctx) error {
		return c.Render("incasari", fiber.Map{}, "base")
	})

	app.Post("/adauga-incasari", func(c *fiber.Ctx) error {

		if form, err := c.MultipartForm(); err == nil {

			serie := form.Value["serie"][0]
			numar := form.Value["numar"][0]
			data := form.Value["data"][0]
			suma_incasata := form.Value["suma_incasata"][0]
			// fisier := form.Value["fisier"][0]

			log.Println(serie)
			log.Println(numar)
			log.Println(data)
			log.Println(suma_incasata)
			// log.Println(fisier)

		}

		return c.Redirect("/adauga-incasari")

	})

}
