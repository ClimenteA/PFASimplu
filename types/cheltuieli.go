package types

type AmortizareMijlocFix struct {
	NumeCheltuiala string  `json:"nume_cheltuiala"`
	SumaCheltuita  float64 `json:"suma_cheltuita"`
	TipTranzactie  string  `json:"tip_tranzactie"`
	Data           string  `json:"data"`
	CaleCheltuiala string  `json:"cale_cheltuiala"`
}

type DetaliiMijlocFix struct {
	AniAmortizare                  int                   `json:"ani_amortizare"`
	DataPuneriiInFunctiune         string                `json:"data_punerii_in_functiune"`
	CodClasificare                 string                `json:"cod_clasificare"`
	NrInventar                     int                   `json:"nr_inventar"`
	FelSerieNumarDataDocument      string                `json:"fel_serie_numar_data_document"`
	ValoareInventar                float64               `json:"valoare_inventar"`
	AmortizareLunara               float64               `json:"amortizare_lunara"`
	DenumireSiCaracteristici       string                `json:"denumire_si_caracteristici"`
	Accesorii                      string                `json:"accesorii"`
	Grupa                          string                `json:"grupa"`
	AnulDariiInFolosinta           int                   `json:"anul_darii_in_folosinta"`
	LunaDariiInFolosinta           int                   `json:"luna_darii_in_folosinta"`
	AnulAmortizariiComplete        int                   `json:"anul_amortizarii_complete"`
	LunaAmortizariiComplete        int                   `json:"luna_amortizarii_complete"`
	DurataNormalaDeFunctionare     string                `json:"durata_normala_de_functionare"`
	CotaDeAmortizare               float64               `json:"cota_de_amortizare"`
	DesfasurareAmortizareMijlocFix []AmortizareMijlocFix `json:"desfasurare_amortizare_mijloc_fix"`
}

type Cheltuiala struct {
	NumeCheltuiala   string           `json:"nume_cheltuiala"`
	SumaCheltuita    float64          `json:"suma_cheltuita"`
	TipTranzactie    string           `json:"tip_tranzactie"`
	Data             string           `json:"data"`
	ObiectInventar   bool             `json:"obiect_inventar"`
	MijlocFix        bool             `json:"mijloc_fix"`
	CaleCheltuiala   string           `json:"cale_cheltuiala"`
	DetaliiMijlocFix DetaliiMijlocFix `json:"detalii_mijloc_fix"`
}
