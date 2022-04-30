// https://ciel.ro/blog/antreprenoriat/mijloacele-fixe-care-sunt-cum-le-deosebesti-de-obiectele-de-inventar-cum-se-amortizeaza-si-cum-se-caseaza-acestea/
package cheltuieli

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"mime/multipart"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/session"
	"github.com/lithammer/shortuuid"
)

func HandleCheltuieli(app fiber.App, store session.Store, coduriMijloaceFixe []staticdata.CodMijloaceFixe) {
	handleCheltuieli(app, store, coduriMijloaceFixe)
}

type AmortizareMijlocFix struct {
	NumeCheltuiala string  `json:"nume_cheltuiala"`
	SumaCheltuita  float64 `json:"suma_cheltuita"`
	TipTranzactie  string  `json:"tip_tranzactie"`
	Data           string  `json:"data"`
	CaleCheltuiala string  `json:"cale_cheltuiala"`
}

type DetaliiMijlocFix struct {
	AniAmortizare                  int                   `json:"ani_amortizare"`
	DataPuneriiInFunctiune         string                `json:"data_punerii_in_functiune"`
	CodClasificare                 string                `json:"cod_clasificare"`
	NrInventar                     int                   `json:"nr_inventar"`
	FelSerieNumarDataDocument      string                `json:"fel_serie_numar_data_document"`
	ValoareInventar                float64               `json:"valoare_inventar"`
	AmortizareLunara               float64               `json:"amortizare_lunara"`
	DenumireSiCaracteristici       string                `json:"denumire_si_caracteristici"`
	Accesorii                      string                `json:"accesorii"`
	Grupa                          string                `json:"grupa"`
	AnulDariiInFolosinta           int                   `json:"anul_darii_in_folosinta"`
	LunaDariiInFolosinta           int                   `json:"luna_darii_in_folosinta"`
	AnulAmortizariiComplete        int                   `json:"anul_amortizarii_complete"`
	LunaAmortizariiComplete        int                   `json:"luna_amortizarii_complete"`
	DurataNormalaDeFunctionare     string                `json:"durata_normala_de_functionare"`
	CotaDeAmortizare               float64               `json:"cota_de_amortizare"`
	DesfasurareAmortizareMijlocFix []AmortizareMijlocFix `json:"desfasurare_amortizare_mijloc_fix"`
}

type Cheltuiala struct {
	NumeCheltuiala   string           `json:"nume_cheltuiala"`
	SumaCheltuita    float64          `json:"suma_cheltuita"`
	TipTranzactie    string           `json:"tip_tranzactie"`
	Data             string           `json:"data"`
	ObiectInventar   bool             `json:"obiect_inventar"`
	MijlocFix        bool             `json:"mijloc_fix"`
	CaleCheltuiala   string           `json:"cale_cheltuiala"`
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

func getDetaliiMijlocFixFromCodCasificare(cod_clasificare string, coduriMijloaceFixe []staticdata.CodMijloaceFixe) staticdata.CodMijloaceFixe {

	detaliiMijlocFix := staticdata.CodMijloaceFixe{}
	for _, item := range coduriMijloaceFixe {
		if cod_clasificare == item.CodClasificare {
			detaliiMijlocFix = item
			break
		}
	}
	return detaliiMijlocFix
}

func calcDesfasurareAmortizare(
	desfasurareAmortizare []AmortizareMijlocFix,
	startDate, endDate time.Time,
	expenseData Cheltuiala,
	amortizare_lunara float64,
) []AmortizareMijlocFix {

	startDate = startDate.AddDate(0, 1, 0)

	for d := startDate; !d.After(endDate); d = d.AddDate(0, 1, 0) {

		data := d.AddDate(0, 0, -d.Day())

		amf := AmortizareMijlocFix{
			NumeCheltuiala: "Amortizare lunara " + expenseData.NumeCheltuiala,
			Data:           data.Format(time.RFC3339)[0:10],
			CaleCheltuiala: expenseData.CaleCheltuiala,
			TipTranzactie:  expenseData.TipTranzactie,
			SumaCheltuita:  amortizare_lunara,
		}

		desfasurareAmortizare = append(desfasurareAmortizare, amf)

	}

	return desfasurareAmortizare
}

func getDetaliiMijlocFix(
	mijloc_fix bool,
	form *multipart.Form,
	filename string,
	expenseData Cheltuiala,
	coduriMijloaceFixe []staticdata.CodMijloaceFixe,
) DetaliiMijlocFix {

	nr_inventar := 0
	fel_serie_numar_data_document := ""
	valoare_inventar := 0.0
	amortizare_lunara := 0.0
	amortizare_in_ani := 0
	accesorii := ""
	grupa := ""
	anul_darii_in_folosinta := 0
	luna_darii_in_folosinta := 0
	anul_amortizarii_complete := 0
	luna_amortizarii_complete := 0
	durata_normala_de_functionare := ""
	cota_de_amortizare := 0.0
	denumire_si_caracteristici := ""
	data_punerii_in_functiune := ""
	cod_clasificare := ""
	desfasurareAmortizare := []AmortizareMijlocFix{}

	if mijloc_fix {

		ani, err := strconv.Atoi(form.Value["amortizare_in_ani"][0])
		if err != nil {
			log.Panicln(err)
		}
		amortizare_in_ani = ani
		data_punerii_in_functiune = form.Value["data_punerii_in_functiune"][0]
		cod_clasificare = form.Value["cod_clasificare"][0]
		fel_serie_numar_data_document = "Factura/Bon " + filename
		valoare_inventar = expenseData.SumaCheltuita
		amortizare_lunara = expenseData.SumaCheltuita / (float64(amortizare_in_ani) * 12)
		denumire_si_caracteristici = "Sunt detaliate in factura/bon"
		accesorii = "Sunt detaliate in factura/bon"

		mijdetalii := getDetaliiMijlocFixFromCodCasificare(cod_clasificare, coduriMijloaceFixe)

		grupa = mijdetalii.Grupa
		durata_normala_de_functionare = mijdetalii.DurataAmortizareInAni
		t, err := time.Parse(time.RFC3339, data_punerii_in_functiune+"T00:00:00Z")
		if err != nil {
			log.Panic(err)
		}

		anul_darii_in_folosinta = t.Year()
		luna_darii_in_folosinta = int(t.Month())

		incepereAmortizareDate := t.AddDate(0, 1, 0)
		amortizareDate := incepereAmortizareDate.AddDate(amortizare_in_ani, 0, 0)
		anul_amortizarii_complete = amortizareDate.Year()
		luna_amortizarii_complete = int(amortizareDate.Month())
		cota_de_amortizare = (amortizare_lunara / expenseData.SumaCheltuita) * 100

		desfasurareAmortizare = calcDesfasurareAmortizare(
			desfasurareAmortizare,
			incepereAmortizareDate,
			amortizareDate,
			expenseData,
			amortizare_lunara,
		)

	}

	detaliiMijlocFix := DetaliiMijlocFix{
		AniAmortizare:                  amortizare_in_ani,
		DataPuneriiInFunctiune:         data_punerii_in_functiune,
		CodClasificare:                 cod_clasificare,
		NrInventar:                     nr_inventar,
		FelSerieNumarDataDocument:      fel_serie_numar_data_document,
		ValoareInventar:                valoare_inventar,
		AmortizareLunara:               amortizare_lunara,
		DenumireSiCaracteristici:       denumire_si_caracteristici,
		Accesorii:                      accesorii,
		Grupa:                          grupa,
		AnulDariiInFolosinta:           anul_darii_in_folosinta,
		LunaDariiInFolosinta:           luna_darii_in_folosinta,
		AnulAmortizariiComplete:        anul_amortizarii_complete,
		LunaAmortizariiComplete:        luna_amortizarii_complete,
		DurataNormalaDeFunctionare:     durata_normala_de_functionare,
		CotaDeAmortizare:               cota_de_amortizare,
		DesfasurareAmortizareMijlocFix: desfasurareAmortizare,
	}

	return detaliiMijlocFix

}

func getExpenseData(c *fiber.Ctx, user auth.Account, form *multipart.Form, filename, cale_cheltuiala string, coduriMijloaceFixe []staticdata.CodMijloaceFixe) Cheltuiala {

	data := form.Value["data"][0]

	nume_cheltuiala := strings.Trim(form.Value["nume_cheltuiala"][0], " ")
	suma_cheltuita, err := strconv.ParseFloat(form.Value["suma_cheltuita"][0], 64)
	if err != nil {
		log.Panic(err)
	}
	tip_tranzactie := form.Value["tip_tranzactie"][0]

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

	expenseData := Cheltuiala{
		NumeCheltuiala: nume_cheltuiala,
		SumaCheltuita:  suma_cheltuita,
		Data:           data,
		TipTranzactie:  tip_tranzactie,
		ObiectInventar: obiect_inventar,
		MijlocFix:      mijloc_fix,
		CaleCheltuiala: cale_cheltuiala,
	}

	detaliiMijlocFix := getDetaliiMijlocFix(mijloc_fix, form, filename, expenseData, coduriMijloaceFixe)
	expenseData.DetaliiMijlocFix = detaliiMijlocFix

	return expenseData

}

func handleCheltuieli(app fiber.App, store session.Store, coduriMijloaceFixe []staticdata.CodMijloaceFixe) {

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

			fisier, err := c.FormFile("fisier")
			if err != nil {
				log.Panic(err)
			}

			data := form.Value["data"][0]

			uid := shortuuid.New()
			dirName := filepath.Join(user.StocareCheltuieli, data, uid)
			expensePath := getExpensePath(dirName)
			cale_cheltuiala := filepath.Join(expensePath, fisier.Filename)
			c.SaveFile(fisier, cale_cheltuiala)

			expenseData := getExpenseData(c, user, form, fisier.Filename, cale_cheltuiala, coduriMijloaceFixe)
			expenseJsonPath := getExpenseJsonPath(dirName)
			setExpenseData(expenseData, expenseJsonPath)

		}

		return c.Redirect("/adauga-cheltuieli?title=Cheltuiala adaugata&content=Cheltuiala a fost adaugata. Vezi registre contabile.")

	})

}
