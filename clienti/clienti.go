package clienti

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/types"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
)

func HandleClientsRequests(app fiber.App, store session.Store) {
	handleClientsRequests(app, store)
}

func getCurrentUser(currentUserPath string) auth.Account {

	var data auth.Account

	jsonFile, err := os.Open(currentUserPath)
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func getCurrentClients(currentUserPath string) []types.DateIdentificare {

	var data []types.DateIdentificare

	jsonFile, err := os.Open(filepath.Join(currentUserPath, "clienti.json"))
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func updateClients(data []types.DateIdentificare, filePath string) {
	file, _ := json.MarshalIndent(data, "", " ")
	err := ioutil.WriteFile(filepath.Join(filePath, "clienti.json"), file, 0644)
	if err != nil {
		panic(err)
	}
}

func getFurnizor(currentUserPath string) types.DateIdentificare {

	var data types.DateIdentificare

	jsonFile, err := os.Open(filepath.Join(currentUserPath, "furnizor.json"))
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func updateFurnizor(data types.DateIdentificare, filePath string) {
	file, _ := json.MarshalIndent(data, "", " ")
	err := ioutil.WriteFile(filepath.Join(filePath, "furnizor.json"), file, 0644)
	if err != nil {
		panic(err)
	}
}

func handleClientsRequests(app fiber.App, store session.Store) {

	app.Get("/clienti", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		allClients := getCurrentClients(user.Stocare)

		return c.JSON(allClients)
	})

	app.Get("/furnizor", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		furnizor := getFurnizor(user.Stocare)

		return c.JSON(furnizor)
	})

	app.Post("/clienti", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		di := new(types.DateIdentificare)

		if err := c.BodyParser(di); err == nil {

			if di.IsClient {

				allClients := getCurrentClients(user.Stocare)

				client := types.DateIdentificare{
					Serie:    di.Serie,
					Numar:    di.Numar,
					Data:     di.Data,
					Suma:     di.Suma,
					Nume:     di.Nume,
					NrRegCom: di.NrRegCom,
					CIF:      di.CIF,
					Adresa:   di.Adresa,
					Telefon:  di.Telefon,
					Email:    di.Email,
					Banca:    di.Banca,
					IBAN:     di.IBAN,
					IsClient: di.IsClient,
				}

				newUser := true
				for _, c := range allClients {
					if c.Email == client.Email {
						newUser = false
						break
					}
				}

				if newUser {
					allClients = append(allClients, client)
				}

				updateClients(allClients, user.Stocare)

			} else {

				furnizor := types.DateIdentificare{
					Serie:    di.Serie,
					Numar:    di.Numar,
					Data:     di.Data,
					Suma:     di.Suma,
					Nume:     di.Nume,
					NrRegCom: di.NrRegCom,
					CIF:      di.CIF,
					Adresa:   di.Adresa,
					Telefon:  di.Telefon,
					Email:    di.Email,
					Banca:    di.Banca,
					IBAN:     di.IBAN,
					IsClient: di.IsClient,
				}

				updateFurnizor(furnizor, user.Stocare)

			}
		}

		return c.Redirect("/clienti")

	})

}
