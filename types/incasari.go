package types

type Factura struct {
	Serie         string  `json:"serie"`
	Numar         int     `json:"numar"`
	Data          string  `json:"data"`
	TipTranzactie string  `json:"tip_tranzactie"`
	SumaIncasata  float64 `json:"suma_incasata"`
	CaleIncasare  string  `json:"cale_incasare"`
}

type ExtraIncasare struct {
	SursaVenit    string  `json:"sursa_venit"`
	Data          string  `json:"data"`
	TipTranzactie string  `json:"tip_tranzactie"`
	SumaIncasata  float64 `json:"suma_incasata"`
	CaleIncasare  string  `json:"cale_incasare"`
}

type FacturaPlusExtraIncasari struct {
	SursaVenit    string  `json:"sursa_venit"`
	Serie         string  `json:"serie"`
	Numar         int     `json:"numar"`
	Data          string  `json:"data"`
	TipTranzactie string  `json:"tip_tranzactie"`
	SumaIncasata  float64 `json:"suma_incasata"`
	CaleIncasare  string  `json:"cale_incasare"`
}
