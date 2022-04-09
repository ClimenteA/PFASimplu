package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/gofiber/storage/badger"
	"github.com/gofiber/template/html"
)

func main() {

	storage := badger.New() // From github.com/gofiber/storage/sqlite3
	store := session.New(session.Config{
		Storage: storage,
	})

	htmlEngine := html.New("./assets/templates", ".html")

	app := fiber.New(fiber.Config{
		Views: htmlEngine,
	})

	app.Use(logger.New())
	app.Static("/", "./assets/public")

	// INDEX

	app.Get("/", func(c *fiber.Ctx) error {
		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		// Set key/value
		sess.Set("name", "heloooooooooooooooooooooooooooo")

		if err := sess.Save(); err != nil {
			panic(err)
		}

		return c.Render("index", fiber.Map{}, "base")
	})

	// LOGIN

	app.Get("/login", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		// Get value
		name := sess.Get("name")

		log.Println(name)

		return c.Render("login", fiber.Map{}, "base")
	})

	app.Post("/login", func(c *fiber.Ctx) error {

		if form, err := c.MultipartForm(); err == nil {

			email := form.Value["email"][0]
			parola := form.Value["parola"][0]

			log.Println(email)
			log.Println(parola)

		}

		return c.Render("login", fiber.Map{}, "base")

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
