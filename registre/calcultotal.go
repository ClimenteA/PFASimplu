package registre

import (
	"fmt"
	"log"
	"strconv"

	"github.com/ClimenteA/pfasimplu-go/declaratii"
	"github.com/ClimenteA/pfasimplu-go/staticdata"
	"github.com/ClimenteA/pfasimplu-go/types"
)

func CalculeazaIncasariBrut(incasari []types.FacturaPlusExtraIncasari) float64 {

	total := 0.0
	for _, data := range incasari {
		total = total + data.SumaIncasata
	}

	return total

}

func CalculeazaCheltuieliDeductibile(cheltuieli []types.Cheltuiala) float64 {

	total := 0.0
	for _, data := range cheltuieli {
		total = total + data.SumaCheltuita
	}
	return total

}

func CalculPlatiFacuteAnaf(declaratii []declaratii.Declaratie, filterYear string) float64 {

	anul, _ := strconv.Atoi(filterYear)

	total := 0.0
	for _, d := range declaratii {
		if d.PtAnul == anul {
			total = total + d.PlataAnaf
		}
	}
	return total
}

type PlatiStat struct {
	CASPensie    float64 `json:"cas_pensie"`
	CASSSanatate float64 `json:"cass_sanatate"`
	ImpozitVenit float64 `json:"impozit_venit"`
	Total        float64 `json:"total"`
}

func CalculeazaPlatiCatreStat(venitNet float64, anul string) PlatiStat {
	// - Calcul Venit Net: `venitNet = totalIncasari - totalCheltuieli - CAS`;
	// - Calcul Impozit pe Venit: `impozitPeVenit = 10% din venitNet`;
	// - Calcul CAS (Pensie):
	// 	* `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` mai mare de 12 salarii minime brute pana in anul 2022 inclusiv;
	// 	* `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` intre 12 si 24 salarii minime brute din anul 2023+;
	// 	* `bazaDeCalculCAS = salariuMinimBrut x 24` - daca `venitNet` mai mare de 24 salarii minime brute din anul 2023+;
	// 	* `CAS = 25% din bazaDeCalculCAS`;
	// - Calcul CASS (Sanatate):
	// 	* `bazaDeCalculCASS = salariuMinimBrut x 12` - daca `venitNet` mai mare de 12 salarii minime brute pana in anul 2022 inclusiv;
	// 	* `bazaDeCalculCASS = salariuMinimBrut x 6` - daca `venitNet` mai mare de 6 salarii minime brute din anul 2023+;
	// 	* `bazaDeCalculCAS = salariuMinimBrut x 12` - daca `venitNet` intre 12 si 24 salarii minime brute din anul 2023+;
	// 	* `bazaDeCalculCAS = salariuMinimBrut x 24` - daca `venitNet` mai mare de 24 salarii minime brute din anul 2023+;
	// 	* `CASS = 10% din bazaDeCalculCASS`;

	anualVars := staticdata.LoadPFAConfig()

	salariuMinimBrut := 0.0
	for idx, data := range anualVars.SalariiMinime {
		strAn := strconv.Itoa(data.An)
		if strAn == anul {
			salariuMinimBrut = float64(anualVars.SalariiMinime[idx].Valoare)
			break
		}
	}

	CAS := 0.0
	CASS := 0.0
	impozitPeVenit := 0.0
	total := 0.0

	anulCurrent, err := strconv.Atoi(anul)
	if err != nil {
		log.Panicln(err)
	}

	plafon6 := salariuMinimBrut * 6
	plafon12 := salariuMinimBrut * 12
	plafon24 := salariuMinimBrut * 24

	if anulCurrent <= 2022 {

		if venitNet > plafon12 {
			CAS = 25 * plafon12 / 100
			CASS = 10 * plafon12 / 100
		}

	} else {

		if venitNet > plafon6 {
			CASS = 10 * plafon6 / 100
		}

		if venitNet > plafon12 || venitNet <= plafon24 {
			CAS = 25 * plafon12 / 100
			CASS = 10 * plafon12 / 100
		}

		if venitNet > plafon24 {
			CAS = 25 * plafon24 / 100
			CASS = 10 * plafon24 / 100
		}
	}

	impozitPeVenit = 10 * (venitNet - CAS) / 100

	total = CAS + CASS + impozitPeVenit

	data := PlatiStat{
		CASPensie:    CAS,
		CASSSanatate: CASS,
		ImpozitVenit: impozitPeVenit,
		Total:        total,
	}

	return data

}

func GetPlatiCatreStatRounded(totalIncasariNet float64, filterYear string, declaratii []declaratii.Declaratie) (map[string]string, float64, float64) {

	platiCatreStat := CalculeazaPlatiCatreStat(totalIncasariNet, filterYear)
	platiFacuteAnaf := CalculPlatiFacuteAnaf(declaratii, filterYear)
	totalPlatiCatreStat := platiCatreStat.Total - platiFacuteAnaf
	if totalPlatiCatreStat < 1 {
		totalPlatiCatreStat = 0
	}
	totalIncasariNet = totalIncasariNet - platiCatreStat.Total
	platiCatreStatRounded := map[string]string{
		"CASPensie":    fmt.Sprintf("%.2f", platiCatreStat.CASPensie),
		"CASSSanatate": fmt.Sprintf("%.2f", platiCatreStat.CASSSanatate),
		"ImpozitVenit": fmt.Sprintf("%.2f", platiCatreStat.ImpozitVenit),
		"Total":        fmt.Sprintf("%.2f", platiCatreStat.Total),
	}

	return platiCatreStatRounded, totalPlatiCatreStat, totalIncasariNet

}
