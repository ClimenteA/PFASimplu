package registre

import (
	"fmt"
	"strconv"
	"time"

	"github.com/ClimenteA/pfasimplu-go/types"
)

// Hackish approach, could be better

var monthMapper = map[string]string{
	"January":   "Ianuarie",
	"February":  "Februarie",
	"March":     "Martie",
	"April":     "Aprilie",
	"May":       "Mai",
	"June":      "Iunie",
	"July":      "Iulie",
	"August":    "August",
	"September": "Septembrie",
	"October":   "Octombrie",
	"November":  "Noiembrie",
	"December":  "Decembrie",
}

var monthIntMapper = map[string]int{
	"January":   1,
	"February":  2,
	"March":     3,
	"April":     4,
	"May":       5,
	"June":      6,
	"July":      7,
	"August":    8,
	"September": 9,
	"October":   10,
	"November":  11,
	"December":  12,
}

func strToFloat(items []string) []float64 {

	itemsFloat := []float64{}

	for _, item := range items {
		if s, err := strconv.ParseFloat(item, 64); err == nil {
			itemsFloat = append(itemsFloat, s)
		}
	}
	return itemsFloat
}

func getIncasariMapper(incasariPeLuni []string) map[string]float64 {

	incasariFloat := strToFloat(incasariPeLuni)

	incasariMapper := map[string]float64{
		"January":   incasariFloat[0],
		"February":  incasariFloat[1],
		"March":     incasariFloat[2],
		"April":     incasariFloat[3],
		"May":       incasariFloat[4],
		"June":      incasariFloat[5],
		"July":      incasariFloat[6],
		"August":    incasariFloat[7],
		"September": incasariFloat[8],
		"October":   incasariFloat[9],
		"November":  incasariFloat[10],
		"December":  incasariFloat[11],
	}

	return incasariMapper

}

func getCheltuieliMapper(cheltuieliPeLuni []string) map[string]float64 {

	cheltuieliFloat := strToFloat(cheltuieliPeLuni)

	cheltuieliMapper := map[string]float64{
		"January":   cheltuieliFloat[0],
		"February":  cheltuieliFloat[1],
		"March":     cheltuieliFloat[2],
		"April":     cheltuieliFloat[3],
		"May":       cheltuieliFloat[4],
		"June":      cheltuieliFloat[5],
		"July":      cheltuieliFloat[6],
		"August":    cheltuieliFloat[7],
		"September": cheltuieliFloat[8],
		"October":   cheltuieliFloat[9],
		"November":  cheltuieliFloat[10],
		"December":  cheltuieliFloat[11],
	}

	return cheltuieliMapper

}

func appendTotalLunarIncasari(incasari []types.FacturaPlusExtraIncasari, incasariPeLuni []string, filterYear string) []types.FacturaPlusExtraIncasari {

	incasariMapper := getIncasariMapper(incasariPeLuni)

	d := time.Now()

	for month, total := range incasariMapper {

		year, err := strconv.Atoi(filterYear)
		if err != nil {
			year = time.Now().Year()
		}

		endOfThisMonth := time.Date(year, time.Month(monthIntMapper[month])+1, 0, 0, 0, 0, 0, d.Location())

		if endOfThisMonth.After(d) {
			continue
		}

		lastDateOfMonth := endOfThisMonth.Format(time.RFC3339)[0:10]

		val := types.FacturaPlusExtraIncasari{
			Data:        lastDateOfMonth,
			Serie:       fmt.Sprintf("%.2f", total) + " RON",
			CaleIncasare: "Total luna " + monthMapper[month] + " (incasari)",
		}

		incasari = append(incasari, val)

	}

	return incasari

}

func appendTotalLunarCheltuieli(cheltuieli []types.Cheltuiala, cheltuieliPeLuni []string, filterYear string) []types.Cheltuiala {

	cheltuieliMapper := getCheltuieliMapper(cheltuieliPeLuni)

	d := time.Now()

	for month, total := range cheltuieliMapper {

		year, err := strconv.Atoi(filterYear)
		if err != nil {
			year = time.Now().Year()
		}

		endOfThisMonth := time.Date(year, time.Month(monthIntMapper[month])+1, 0, 0, 0, 0, 0, d.Location())

		if endOfThisMonth.After(d) {
			continue
		}

		lastDateOfMonth := endOfThisMonth.Format(time.RFC3339)[0:10]

		val := types.Cheltuiala{
			Data:           lastDateOfMonth,
			NumeCheltuiala: fmt.Sprintf("%.2f", total) + " RON",
			CaleCheltuiala: "Total luna " + monthMapper[month] + " (cheltuieli)",
		}

		cheltuieli = append(cheltuieli, val)

	}

	return cheltuieli

}
