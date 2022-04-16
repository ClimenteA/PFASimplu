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

	"github.com/ClimenteA/pfasimplu-go/mijloacefixe"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

func HandleCheltuieli(app fiber.App, store session.Store, coduriMijloaceFixe mijloacefixe.CodMijloaceFixe) {
	handleCheltuieli(app, store, coduriMijloaceFixe)
}

type Account struct {
	Email   string `json:"email"`
	Parola  string `json:"parola"`
	Stocare string `json:"stocare"`
}

type DetaliiMijlocFix struct {
	AniAmortizare          int64  `json:"ani_amortizare"`
	DataPuneriiInFunctiune string `json:"data_punerii_in_functiune"`
	CodClasificare         string `json:"cod_clasificare"`
}

type Cheltuiala struct {
	NumeCheltuiala   string           `json:"nume_cheltuiala"`
	SumaCheltuita    float64          `json:"suma_cheltuita"`
	TipTranzactie    string           `json:"tip_tranzactie"`
	Data             string           `json:"data"`
	ObiectInventar   bool             `json:"obiect_inventar"`
	MijlocFix        bool             `json:"mijloc_fix"`
	DetaliiMijlocFix DetaliiMijlocFix `json:"detalii_mijloc_fix"`
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

func handleCheltuieli(app fiber.App, store session.Store, coduriMijloaceFixe mijloacefixe.CodMijloaceFixe) {

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

			obiect_inventar := false
			inv, keyExists := form.Value["inventar"]
			if keyExists {
				obiect_inventar = true
			}

			if keyExists {
				log.Println("Obiect de inventar")
				log.Println(inv)
			}

			mijloc_fix := false
			mfix, keyExists := form.Value["mijlocfix"]
			if keyExists {
				mijloc_fix = true
				log.Println(mfix)
			}

			amortizare_in_ani := 0
			data_punerii_in_functiune := ""
			cod_clasificare := ""
			if mijloc_fix {

				ani, err := strconv.Atoi(form.Value["amortizare_in_ani"][0])
				if err != nil {
					log.Panicln(err)
				}
				amortizare_in_ani = ani
				data_punerii_in_functiune = form.Value["data_punerii_in_functiune"][0]
				cod_clasificare = form.Value["cod_clasificare"][0]

			}

			expenseData := Cheltuiala{
				NumeCheltuiala: nume_cheltuiala,
				SumaCheltuita:  suma_cheltuita,
				Data:           data,
				TipTranzactie:  tip_tranzactie,
				ObiectInventar: obiect_inventar,
				MijlocFix:      mijloc_fix,
				DetaliiMijlocFix: DetaliiMijlocFix{
					AniAmortizare:          int64(amortizare_in_ani),
					DataPuneriiInFunctiune: data_punerii_in_functiune,
					CodClasificare:         cod_clasificare,
				},
			}

			expenseJsonPath := getExpenseJsonPath(dirName)
			setExpenseData(expenseData, expenseJsonPath)

			expensePath := getExpensePath(dirName)
			c.SaveFile(fisier, filepath.Join(expensePath, fisier.Filename))

		}

		return c.Redirect("/adauga-cheltuieli")

	})

}
