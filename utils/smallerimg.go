package utils

import (
	"image/jpeg"
	"log"
	"os"
	"strings"

	"github.com/nfnt/resize"
)

func SmallerImg(path string) {

	if strings.HasSuffix(path, ".jpeg") && strings.HasSuffix(path, ".jpg") {

		file, err := os.Open(path)
		if err != nil {
			log.Fatal(err)
		}

		img, err := jpeg.Decode(file)
		if err != nil {
			log.Fatal(err)
		}
		file.Close()

		m := resize.Resize(3000, 0, img, resize.Lanczos3)

		out, err := os.Create(path)
		if err != nil {
			log.Fatal(err)
		}
		defer out.Close()

		jpeg.Encode(out, m, nil)

	} else {
		log.Println("Not a jpg format, can't shrink image " + path)
	}

}
