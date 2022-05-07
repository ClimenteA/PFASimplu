package registre

import (
	"math"
	"strings"
	"time"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/extrasbancar"
)

func AdunaComisioaneBancare(user auth.Account, anul string) float64 {

	extrasING := extrasbancar.DateING(user, anul)
	totalComisioane := 0.0
	now := time.Now()
	for _, rows := range extrasING {
		for _, row := range rows {

			iterDate, _ := time.Parse(time.RFC3339, row.DataProcesarii+"T00:00:00Z")

			isBeforeNow := iterDate.Before(now)
			sameMonthYear := iterDate.Year() == now.Year() && iterDate.Month() == now.Month()

			if isBeforeNow || sameMonthYear {

				if strings.Contains(row.AdresaBeneficiar, "ING Bank Romania") && strings.HasPrefix(row.DataProcesarii, anul) {
					totalComisioane = totalComisioane + math.Abs(row.Suma)
				}

			}
		}
	}

	return totalComisioane

}
