run:
	nodemon --exec go run main.go --signal SIGTERM
build:
	rm -rf dist 
	GOOS=windows GOARCH=amd64 go build -o dist/PFASimplu-Windows-64bit/pfasimplu.exe main.go
	GOOS=linux GOARCH=amd64 go build -o dist/PFASimplu-Linux-64bit/pfasimplu main.go
	GOOS=darwin GOARCH=amd64 go build -o dist/PFASimplu-MacOS-64bit/pfasimplu main.go
	cp -r assets dist/PFASimplu-Windows-64bit/
	cp -r assets dist/PFASimplu-Linux-64bit/
	cp -r assets dist/PFASimplu-MacOS-64bit/
	cp -r INSTRUCTIUNI-WINDOWS.txt dist/PFASimplu-Windows-64bit/INSTRUCTIUNI.txt
	cp -r INSTRUCTIUNI-LINUX.txt dist/PFASimplu-Linux-64bit/INSTRUCTIUNI.txt
	cp -r INSTRUCTIUNI-MAC.txt dist/PFASimplu-MacOS-64bit/INSTRUCTIUNI.txt
	mkdir dist/PFASimplu
	cp dist/PFASimplu-Windows-64bit/pfasimplu.exe dist/PFASimplu/pfasimplu-win.exe
	cp dist/PFASimplu-Linux-64bit/pfasimplu dist/PFASimplu/pfasimplu-nix.exe
	cp dist/PFASimplu-MacOS-64bit/pfasimplu dist/PFASimplu/pfasimplu-mac.exe
	cp -r assets dist/PFASimplu/
	cp -r INSTRUCTIUNI-WINDOWS.txt dist/PFASimplu/INSTRUCTIUNI-WIN.txt
	cp -r INSTRUCTIUNI-LINUX.txt dist/PFASimplu/INSTRUCTIUNI-NIX.txt
	cp -r INSTRUCTIUNI-MAC.txt dist/PFASimplu/INSTRUCTIUNI-MAC.txt
