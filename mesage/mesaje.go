package mesage

import (
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleMesaje(app fiber.App, store session.Store, title, description, redirectLink string) {

	app.Get("/mesaje", func(c *fiber.Ctx) error {
		return c.Render("success", fiber.Map{
			"Title":        title,
			"Description":  description,
			"RedirectLink": redirectLink,
		}, "base")
	})
}
