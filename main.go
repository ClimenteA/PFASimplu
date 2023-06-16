package main

// Docs
// https://docs.gofiber.io/
// https://github.com/gofiber/template/tree/master/html
// https://github.com/gofiber/template/blob/master/html/TEMPLATES_CHEATCHEET.md#golang-templates-cheatsheet

import (
	"fmt"
	"log"
	"strconv"

	"github.com/ClimenteA/fiberwebgui"
	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/cheltuieli"
	"github.com/ClimenteA/pfasimplu-go/clienti"
	"github.com/ClimenteA/pfasimplu-go/declaratieanaf"
	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/ClimenteA/pfasimplu-go/download"
	"github.com/ClimenteA/pfasimplu-go/factura"
	"github.com/ClimenteA/pfasimplu-go/incasari"
	"github.com/ClimenteA/pfasimplu-go/incasariextra"
	"github.com/ClimenteA/pfasimplu-go/inventar"
	"github.com/ClimenteA/pfasimplu-go/landing"
	"github.com/ClimenteA/pfasimplu-go/registre"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/ClimenteA/pfasimplu-go/updates"
	"github.com/ClimenteA/pfasimplu-go/utils"
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
	declaratieanaf.HandleDeclaratie212(*app, *store)
	download.HandleDownloadDateCont(*app, *store)
	landing.HandleLandingPage(*app, *store)
	factura.HandleInvoicePage(*app, *store)
	clienti.HandleClientsRequests(*app, *store)
	inventar.HandleInventarPage(*app, *store)
	incasariextra.HandleIncasariExtra(*app, *store)
	updates.HandleUpdatesPage(*app, *store)

	hostIp := utils.GetHostIp()
	config := staticdata.LoadPFAConfig()

	fmt.Println("\nAplicatia PFASimplu v" + config.VersiuneAplicatie)
	fmt.Println("Pastreaza aceasta fereastra deschisa cat timp folosesti aplicatia!")

	if config.Environment == "desktop" {
		portstr := strconv.Itoa(config.Port)
		fmt.Println("\n\nPoti vedea aplicatia in browser la addresa:\nhttp://localhost:" + portstr + " (pe acest dispozitiv)")
		fmt.Println("\nSau poti intra de pe telefon/tableta/laptop in browser pe addresa:\n" + "http://" + hostIp + ":" + portstr)
		fiberwebgui.RunBrowserOnPort(app, config.Port)
	} else {
		fmt.Println("\n\nPoti vedea aplicatia in browser la addresa:\nhttp://localhost:3000 (pe acest dispozitiv)")
		fmt.Println("\nSau poti intra de pe telefon/tableta/laptop in browser pe addresa:\n" + "http://" + hostIp + ":3000")
		log.Fatal(app.Listen("0.0.0.0:3000"))
	}
}
