package types

type DateIdentificare struct {
	Serie    string  `json:"serie"`
	Numar    int     `json:"numar"`
	Data     string  `json:"data"`
	Suma     float64 `json:"suma"`
	Nume     string  `json:"nume"`
	NrRegCom string  `json:"nrRegCom"`
	CIF      string  `json:"cif"`
	Adresa   string  `json:"adresa"`
	Telefon  string  `json:"telefon"`
	Email    string  `json:"email"`
	IBAN     string  `json:"iban"`
	IsClient bool    `json:"is_client"`
}
