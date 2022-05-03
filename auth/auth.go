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

func HandleAuth(app fiber.App, store session.Store) {

	handleIndex(app, store)
	handleLogin(app, store)
	handleRegister(app, store)
	handleLogout(app, store)
	handleResetPassword(app, store)

}

type Account struct {
	Email             string `json:"email"`
	Parola            string `json:"parola"`
	Stocare           string `json:"stocare"`
	StocareIncasari   string `json:"stocare_incasari"`
	StocareCheltuieli string `json:"stocare_cheltuieli"`
	StocareDeclaratii string `json:"stocare_declaratii"`
}

func encryptData(dataStr string) string {

	data := []byte(dataStr)
	hash := sha256.Sum256(data)

	encryptedString := hex.EncodeToString(hash[:])

	return encryptedString

}

func getAccountPath(accountName string) string {
	dirPath := filepath.Join("stocare", "conturi")
	accountPath := filepath.Join("stocare", accountName)
	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, accountName+".json")
	} else {
		os.MkdirAll(dirPath, 0750)
		os.MkdirAll(accountPath, 0750)
		return filepath.Join(dirPath, accountName+".json")
	}
}

func setAccountData(accountFilePath, email, parola, stocare string) Account {

	stocareIncasari := filepath.Join(stocare, "incasari")
	stocareCheltuieli := filepath.Join(stocare, "cheltuieli")
	stocareDeclaratii := filepath.Join(stocare, "declaratii")

	if _, err := os.Stat(stocare); err != nil || !os.IsExist(err) {
		os.MkdirAll(stocare, 0750)
	}

	if _, err := os.Stat(stocareIncasari); err != nil || !os.IsExist(err) {
		os.MkdirAll(stocareIncasari, 0750)
	}

	if _, err := os.Stat(stocareCheltuieli); err != nil || !os.IsExist(err) {
		os.MkdirAll(stocareCheltuieli, 0750)
	}

	if _, err := os.Stat(stocareDeclaratii); err != nil || !os.IsExist(err) {
		os.MkdirAll(stocareDeclaratii, 0750)
	}

	data := Account{
		Email:             email,
		Parola:            parola,
		Stocare:           stocare,
		StocareIncasari:   stocareIncasari,
		StocareCheltuieli: stocareCheltuieli,
		StocareDeclaratii: stocareDeclaratii,
	}

	file, _ := json.MarshalIndent(data, "", " ")
	err := ioutil.WriteFile(accountFilePath, file, 0644)
	if err != nil {
		panic(err)
	}
	return data
}

func getAccountData(accountFilePath string) Account {

	var data Account

	jsonFile, err := os.Open(accountFilePath)
	if err != nil {
		log.Panic(err)
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
				setAccountData(accountFilePath, email, "reset", filepath.Join("stocare", accountName))
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
				return c.Redirect("/register?title=Parolele nu corespund&content=Parolele trebuie sa corespunda si sa fie de minim 6 caractere.")
			}

			accountName := shortuuid.NewWithNamespace(email)
			accountPassword := encryptData(parola)
			accountFilePath := getAccountPath(accountName)

			if _, err := os.Stat(accountFilePath); err == nil || os.IsExist(err) {
				return c.Redirect("/reset-password")
			} else {
				setAccountData(accountFilePath, email, accountPassword, filepath.Join("stocare", accountName))
			}
		}

		return c.Redirect("/login?title=Contul a fost creat&content=Intra cu credentialele contului")

	})

}

func handleLogin(app fiber.App, store session.Store) {

	app.Get("/login", func(c *fiber.Ctx) error {
		return c.Render("login", fiber.Map{})
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
				accountData := getAccountData(accountFilePath)
				if accountData.Parola == accountPassword {
					sess.Set("currentUser", accountFilePath)
					if err := sess.Save(); err != nil {
						panic(err)
					}
				}
			} else {
				return c.Redirect("/login?title=Date autentificare gresite&content=Parola sau emailul nu corespund sau contul nu exista")
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
		currentUser := sess.Get("currentUser")
		if currentUser == nil {
			return c.Redirect("/landing")
		}
		return c.Render("index", fiber.Map{}, "base")
	})
}
