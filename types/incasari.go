package types

type Factura struct {
	Serie         string  `json:"serie"`
	Numar         int     `json:"numar"`
	Data          string  `json:"data"`
	TipTranzactie string  `json:"tip_tranzactie"`
	SumaIncasata  float64 `json:"suma_incasata"`
	CaleFactura   string  `json:"cale_factura"`
}
