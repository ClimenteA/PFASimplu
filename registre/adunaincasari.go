package registre

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
)

func AdunaIncasari(user Account) (Account, error) {

	


	err := filepath.Walk(filepath.Join(user.Stocare, "incasari"),
		func(path string, _ os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			fmt.Println(path)

			return nil
		})

	if err != nil {
		log.Println(err)
	}

	return user, err
}
