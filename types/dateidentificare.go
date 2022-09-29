package types

type DateIdentificare struct {
	Serie    string  `json:"serie"`
	Numar    int     `json:"numar"`
	Data     string  `json:"data"`
	Suma     float64 `json:"suma"`
	Nume     string  `json:"nume"`
	NrRegCom string  `json:"nr_reg_com"`
	CIFVAT   string  `json:"cif_vat"`
	Adresa   string  `json:"adresa"`
	Telefon  string  `json:"telefon"`
	Email    string  `json:"email"`
	IBAN     string  `json:"iban"`
	IsClient bool    `json:"is_client"`
}
