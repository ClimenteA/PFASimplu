package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md

import (
	"log"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/gofiber/template/html"
)

func main() {

	htmlEngine := html.New("./assets/templates", ".html")

	store := session.New()

	app := fiber.New(fiber.Config{
		Views: htmlEngine,
	})

	app.Use(logger.New())
	app.Static("/", "./assets/public")

	auth.HandleAuth(*app, *store)
	incasari.HandleIncasari(*app, *store)

	// CHELTUIELI

	app.Get("/adauga-cheltuieli", func(c *fiber.Ctx) error {
		return c.Render("cheltuieli", fiber.Map{}, "base")
	})

	app.Post("/adauga-cheltuieli", func(c *fiber.Ctx) error {
		return c.Render("cheltuieli", fiber.Map{}, "base")
	})

	// DECLARATII

	app.Get("/adauga-declaratii", func(c *fiber.Ctx) error {
		return c.Render("declaratii", fiber.Map{}, "base")
	})

	app.Post("/adauga-declaratii", func(c *fiber.Ctx) error {
		return c.Render("declaratii", fiber.Map{}, "base")
	})

	log.Fatal(app.Listen(":3000"))

}
