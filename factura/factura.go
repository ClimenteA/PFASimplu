package factura

import (
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleInvoicePage(app fiber.App, store session.Store) {
	handleInvoicePage(app, store)
}

func handleInvoicePage(app fiber.App, store session.Store) {

	app.Get("/factura", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			c.Redirect("/login")
		}

		return c.Render("factura", fiber.Map{}, "base")
	})

}
