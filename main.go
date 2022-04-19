package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md#golang-templates-cheatsheet

import (
	"log"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/ClimenteA/pfasimplu-go/registre"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/gofiber/template/html"
)

func main() {

	htmlEngine := html.New("./assets/templates", ".html")
	coduriMijloaceFixe := staticdata.LoadMijloaceFixe()

	store := session.New()

	app := fiber.New(fiber.Config{
		Views: htmlEngine,
	})

	app.Use(logger.New())
	app.Static("/", "./assets/public")

	auth.HandleAuth(*app, *store)
	incasari.HandleIncasari(*app, *store)
	cheltuieli.HandleCheltuieli(*app, *store, coduriMijloaceFixe)
	declaratii.HandleDeclaratii(*app, *store)
	registre.HandleRegistre(*app, *store)

	log.Fatal(app.Listen(":3000"))

}
