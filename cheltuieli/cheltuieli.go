package cheltuieli

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

func HandleCheltuieli(app fiber.App, store session.Store) {
	handleCheltuieli(app, store)
}

type Account struct {
	Email   string `json:"email"`
	Parola  string `json:"parola"`
	Stocare string `json:"stocare"`
}

type Cheltuiala struct {
	NumeCheltuiala string `json:"nume_cheltuiala"`
	SumaCheltuita  string `json:"suma_cheltuita"`
	TipTranzactie  string `json:"tip_tranzactie"`
	NumeCheltuiala string `json:"nume_cheltuiala"`
	NumeCheltuiala string `json:"nume_cheltuiala"`
	NumeCheltuiala string `json:"nume_cheltuiala"`
	NumeCheltuiala string `json:"nume_cheltuiala"`
}

func getExpenseJsonPath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return filepath.Join(dirPath, "metadata.json")
	} else {
		os.MkdirAll(dirPath, 0750)
		return filepath.Join(dirPath, "metadata.json")
	}
}

func getExpensePath(dirPath string) string {

	if _, err := os.Stat(dirPath); err == nil || os.IsExist(err) {
		return dirPath
	} else {
		os.MkdirAll(dirPath, 0750)
		return dirPath
	}

}

func setExpenseData(expenseData Cheltuiala, filePath string) {
	file, _ := json.MarshalIndent(expenseData, "", " ")
	err := ioutil.WriteFile(filePath, file, 0644)
	if err != nil {
		log.Panic(err)
	}
}

func getCurrentUser(currentUserPath string) Account {

	var data Account

	jsonFile, err := os.Open(currentUserPath)
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	return data
}

func handleCheltuieli(app fiber.App, store session.Store) {

	app.Get("/adauga-cheltuieli", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			log.Panic(err)
		}

		if sess.Get("currentUser") == nil {
			return c.Redirect("/login")
		}

		return c.Render("cheltuieli", fiber.Map{}, "base")
	})

	app.Post("/adauga-cheltuieli", func(c *fiber.Ctx) error {

		sess, err := store.Get(c)
		if err != nil {
			log.Panic(err)
		}

		currentUserPath := sess.Get("currentUser")
		if currentUserPath == nil {
			return c.Redirect("/login")
		}

		user := getCurrentUser(fmt.Sprint(currentUserPath))

		if form, err := c.MultipartForm(); err == nil {

			// let tip_tranzactie = request.bodyParam("tip_tranzactie")
			// let inventar = request.bodyParam("inventar")
			// let data = request.bodyParam("data")
			// let fisier = request.bodyParam("fisier")

			// let mijlocfix = request.bodyParam("mijlocfix")
			// let amortizare_in_ani = request.bodyParam("amortizare_in_ani")
			// let data_punerii_in_functiune = request.bodyParam("data_punerii_in_functiune")
			// let cod_clasificare = request.bodyParam("cod_clasificare")

			data := form.Value["data"][0]

			uid := shortuuid.New()
			dirName := filepath.Join(user.Stocare, "cheltuieli", data, uid)

			nume_cheltuiala := strings.Trim(form.Value["nume_cheltuiala"][0], " ")
			suma_cheltuita, err := strconv.ParseFloat(form.Value["suma_cheltuita"][0], 64)
			if err != nil {
				log.Panic(err)
			}
			tip_tranzactie := form.Value["tip_tranzactie"][0]

			fisier, err := c.FormFile("fisier")
			if err != nil {
				log.Panic(err)
			}

			obiectDeInventar := false
			inv, keyExists := form.Value["inventar"]
			if keyExists {
				obiectDeInventar = true
			}

			if obiectDeInventar {
				log.Println("Obiect de inventar")
			}

			mijlocFix := false
			mfix, keyExists := form.Value["mijlocfix"]
			if keyExists {
				mijlocFix = true
			}

			if mijlocFix {
				log.Println("Mijloc Fix")

				amortizare_in_ani, err := strconv.Atoi(form.Value["amortizare_in_ani"][0])
				if err != nil {
					log.Panicln(err)
				}

				data_punerii_in_functiune := form.Value["data_punerii_in_functiune"][0]
				cod_clasificare := form.Value["cod_clasificare"][0]

				log.Println("amortizare_in_ani: ", amortizare_in_ani)
				log.Println(data_punerii_in_functiune)
				log.Println(cod_clasificare)

			}

			log.Println(nume_cheltuiala)
			log.Println(suma_cheltuita)
			log.Println(tip_tranzactie)
			log.Println(data)
			log.Println(fisier.Filename)
			log.Println(inv)
			log.Println(mfix)
			log.Panicln(dirName)

			// expenseData := Cheltuiala{
			// 	Serie:         serie,
			// 	Numar:         numar,
			// 	Data:          data,
			// 	SumaCheltuita: suma_incasata,
			// }

			// expenseJsonPath := getExpenseJsonPath(dirName)
			// setExpenseData(expenseData, expenseJsonPath)

			// expensePath := getExpensePath(dirName)
			// c.SaveFile(fisier, filepath.Join(expensePath, fisier.Filename))

		}

		return c.Redirect("/adauga-cheltuieli")

	})

}
