package types

type RegistruFiscal struct {
	NrCrt             int     `json:"nr_crt"`
	ElemDeCalculVenit string  `json:"elemente_de_calcul_pentru_stabilirea_venitului_net_anual_pierderi_nete_anuale"`
	ValoareRon        float64 `json:"valoarea_ron"`
	Anul              int     `json:"anul"`
}

type RegistruInventar struct {
	NrCrt            int     `json:"nr_crt"`
	DenumireaElemInv string  `json:"denumirea_elementelor_inventariate"`
	ValInvRon        float64 `json:"valoarea_de_inventar_ron"`
}

type RegistruJurnal struct {
	NrCrt                      int     `json:"nr_crt"`
	Data                       string  `json:"data"`
	DocumentFelNr              string  `json:"document_fel_numar"`
	FelulOperatiuniiExplicatii string  `json:"felul_operatiunii_explicatii"`
	IncasariNumerar            float64 `json:"incasari_numerar"`
	IncasariBanca              float64 `json:"incasari_banca"`
	PlatiNumerar               float64 `json:"plati_numerar"`
	PlatiBanca                 float64 `json:"PlatiBanca"`
}
