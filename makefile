run:
	nodemon --exec go run main.go --signal SIGTERM
build:
	go build main.go