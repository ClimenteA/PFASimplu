package incasari

import (
	"fmt"
	"time"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func AddIncasariPeLuni(incasari []types.FacturaPlusExtraIncasari, anul string) []string {

	startDate, err := time.Parse(time.RFC3339, anul+"-01-01T00:00:00Z")
	if err != nil {
		panic(err)
	}
	endDate, err := time.Parse(time.RFC3339, anul+"-12-31T00:00:00Z")
	if err != nil {
		panic(err)
	}

	totalPerMonth := []string{}
	for d := startDate; !d.After(endDate); d = d.AddDate(0, 1, 0) {

		totalMonth := 0.0
		for _, data := range incasari {
			cdate, _ := time.Parse(time.RFC3339, data.Data+"T00:00:00Z")

			if d.Month() == cdate.Month() {

				totalMonth += data.SumaIncasata
			}
		}

		totalPerMonth = append(totalPerMonth, fmt.Sprintf("%2f", totalMonth))

	}

	return totalPerMonth
}
