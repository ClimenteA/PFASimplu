package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/template/html"
)

func main() {

	htmlEngine := html.New("./templates", ".html")

	app := fiber.New(fiber.Config{
		Views: htmlEngine,
	})

	app.Use(logger.New())
	app.Static("/", "./static")

	app.Get("/", func(c *fiber.Ctx) error {
		return c.Render("index", fiber.Map{}, "base")
	})

	// INCASARI
	app.Get("/adauga-incasari", func(c *fiber.Ctx) error {
		return c.Render("incasari", fiber.Map{}, "base")
	})

	app.Post("/adauga-incasari", func(c *fiber.Ctx) error {
		return c.Render("incasari", fiber.Map{}, "base")
	})

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
