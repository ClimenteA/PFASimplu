package registre

import (
	"math"
	"strings"

	"github.com/ClimenteA/pfasimplu-go/auth"
	"github.com/ClimenteA/pfasimplu-go/extrasbancar"
)

func AdunaComisioaneBancare(user auth.Account, anul string) float64 {

	extrasING := extrasbancar.DateING(user, anul)
	totalComisioane := 0.0
	for _, rows := range extrasING {
		for _, row := range rows {
			if strings.Contains(row.AdresaBeneficiar, "ING Bank Romania") && strings.HasPrefix(row.DataProcesarii, anul) {
				totalComisioane = totalComisioane + math.Abs(row.Suma)
			}
		}
	}

	return totalComisioane

}
