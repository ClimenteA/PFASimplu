package tabelpdf

import (
	"path/filepath"

	"github.com/ClimenteA/pfasimplu-go/types"
)

func CreeazaIncasariPDF(path, filterYear string, incasari []types.FacturaPlusExtraIncasari) string {

	pdfPath := filepath.Join(path, filterYear+"_incasari.pdf")

	return pdfPath
}
