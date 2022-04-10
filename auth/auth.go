package auth

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid/v4"
)

func Handle(app fiber.App, store session.Store) {

	handleIndex(app, store)
	handleLogin(app, store)
	handleRegister(app, store)
	handleLogout(app, store)
	handleResetPassword(app, store)

}

type Account struct {
	Email  string `json:"email"`
	Parola string `json:"parola"`
}

func encryptData(dataStr string) string {

	data := []byte(dataStr)
	hash := sha256.Sum256(data)

	encryptedString := hex.EncodeToString(hash[:])

	return encryptedString

}

func getAccountPath(accountName string) string {
	return filepath.Join("storage", "accounts", accountName+".json")
}

func setAccountData(accountFilePath, email, parola string) Account {
	data := Account{Email: email, Parola: parola}
	file, _ := json.MarshalIndent(data, "", " ")
	_ = ioutil.WriteFile(accountFilePath, file, 0644)
	return data
}

func getAccountData(accountFilePath string) Account {

	var data Account

	jsonFile, err := os.Open(accountFilePath)
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func handleResetPassword(app fiber.App, store session.Store) {

	app.Get("/reset-password", func(c *fiber.Ctx) error {
		return c.Render("reset", fiber.Map{}, "base")
	})

	app.Post("/reset-password", func(c *fiber.Ctx) error {

		if form, err := c.MultipartForm(); err == nil {

			email := form.Value["email"][0]
			accountName := shortuuid.NewWithNamespace(email)
			accountFilePath := getAccountPath(accountName)

			if _, err := os.Stat(accountFilePath); err == nil || os.IsExist(err) {
				setAccountData(accountFilePath, email, "reset")
			} else {
				return c.Redirect("/register")
			}
		}

		return c.Redirect("/login")

	})

}

func handleRegister(app fiber.App, store session.Store) {

	app.Get("/register", func(c *fiber.Ctx) error {
		return c.Render("register", fiber.Map{}, "base")
	})

	app.Post("/register", func(c *fiber.Ctx) error {

		if form, err := c.MultipartForm(); err == nil {

			email := form.Value["email"][0]
			parola := form.Value["parola"][0]
			confirmaParola := form.Value["confirmaParola"][0]

			if parola != confirmaParola || len(parola) < 6 {
				return c.Redirect("/register")
			}

			accountName := shortuuid.NewWithNamespace(email)
			accountPassword := encryptData(parola)
			accountFilePath := getAccountPath(accountName)

			if _, err := os.Stat(accountFilePath); err == nil || os.IsExist(err) {
				log.Printf("Account exists: %s", email)
				return c.Redirect("/reset-password")
			} else {
				log.Printf("Creating account: %s", email)
				setAccountData(accountFilePath, email, accountPassword)
			}
		}

		return c.Redirect("/login")

	})

}

func handleLogin(app fiber.App, store session.Store) {

	app.Get("/login", func(c *fiber.Ctx) error {
		return c.Render("login", fiber.Map{}, "base")
	})

	app.Post("/login", func(c *fiber.Ctx) error {

		if form, err := c.MultipartForm(); err == nil {

			sess, err := store.Get(c)
			if err != nil {
				panic(err)
			}

			email := form.Value["email"][0]
			parola := form.Value["parola"][0]

			accountName := shortuuid.NewWithNamespace(email)
			accountPassword := encryptData(parola)
			accountFilePath := getAccountPath(accountName)

			if _, err := os.Stat(accountFilePath); err == nil || os.IsExist(err) {
				log.Printf("Account exists: %s", email)
				accountData := getAccountData(accountFilePath)
				if accountData.Parola == accountPassword {
					sess.Set("authToken", shortuuid.New())
					if err := sess.Save(); err != nil {
						panic(err)
					}
				}
			}
		}

		return c.Redirect("/")

	})

}

func handleLogout(app fiber.App, store session.Store) {

	app.Get("/logout", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		sess.Destroy()

		return c.Redirect("/")
	})
}

func handleIndex(app fiber.App, store session.Store) {

	app.Get("/", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			panic(err)
		}

		authToken := sess.Get("authToken")

		if authToken == nil {
			return c.Redirect("/login")
		}

		return c.Render("index", fiber.Map{}, "base")

	})
}
