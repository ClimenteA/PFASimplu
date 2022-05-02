package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md#golang-templates-cheatsheet

import (
	"fmt"
	"log"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/declaratieanaf"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/ClimenteA/pfasimplu-go/registre"
	"github.com/ClimenteA/pfasimplu-go/sold"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/ClimenteA/pfasimplu-go/utils"
	"github.com/ClimenteA/pfasimplu-go/download"
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
	sold.HandleSoldIntermediar(*app, *store)
	declaratieanaf.HandleDeclaratie212(*app, *store)
	download.HandleDownloadDateCont(*app, *store)

	hostIp := utils.GetHostIp()

	fmt.Println("\nAplicatia PFASimplu!")
	fmt.Println("\n\nPoti vedea aplicatia in browser la addresa:\nhttp://localhost:3000 (pe acest dispozitiv)")
	fmt.Println("\nSau poti intra de pe telefon/tableta/laptop in browser pe addresa:\n" + "http://" + hostIp + ":3000")

	log.Fatal(app.Listen("0.0.0.0:3000"))

}
