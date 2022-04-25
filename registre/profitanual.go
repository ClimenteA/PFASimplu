package registre

import (
	"math"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/extrasbancar"
)

// type TranzactiiBancare struct {
// 	TotalCheltuieli float64 `json:"total_cheltuieli"`
// 	TotalIncasari   float64 `json:"total_incasari"`
// 	TotalProfit     float64 `json:"total_profit"`
// }

func CalculeazaProfitAnual(user auth.Account, anul string) float64 {

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
