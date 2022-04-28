package registre

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"math"
	"os"
	"path/filepath"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/extrasbancar"
	"github.com/ClimenteA/pfasimplu-go/sold"
)

func getSoldIng(user auth.Account, anul string) float64 {

	extrasING := extrasbancar.DateING(user, anul)
	totalProfit := 0.0
	for _, rows := range extrasING {
		for _, row := range rows {
			if strings.HasPrefix(row.DataProcesarii, anul) {

				totalCheltuieli := 0.0
				totalIncasari := 0.0

				if row.Suma < 0 {
					totalCheltuieli = totalCheltuieli + math.Abs(row.Suma)
				} else {
					totalIncasari = totalIncasari + row.Suma
				}

				totalProfit = totalProfit + (totalIncasari - totalCheltuieli)
			}
		}
	}

	return totalProfit

}

func getSoldRegistered(user auth.Account, anul string) float64 {

	var data sold.SoldIntermediar

	soldJson := filepath.Join(user.Stocare, anul+"_sold.json")

	jsonFile, err := os.Open(soldJson)
	if err != nil {
		log.Println(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	json.Unmarshal(byteValue, &data)

	totalProfit := data.Sold

	return totalProfit

}

func CalculeazaProfitAnual(user auth.Account, anul string) float64 {

	soldIng := getSoldIng(user, anul)

	if soldIng > 0 {
		return soldIng
	} else {
		return getSoldRegistered(user, anul)
	}
}
