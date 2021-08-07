package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"syscall"
)

const (
	listenAddr = ":55655"
	pipeIn     = `./pipeVolume/pipe-in`
	pipeOut    = `./pipeVolume/pipe-out`
)

var startChan  = make(chan string)
var answerChan = make(chan []byte)

type PipeRequestStruct struct {
	Action string `json:"action"`
	Str    string `json:"str"`
}

func listener() {
	for {
		byteData, _ := os.ReadFile(pipeIn)
		var requestData PipeRequestStruct
		_ = json.Unmarshal(byteData, &requestData)
		if requestData.Action == "start" {
			select {
				case startChan <- requestData.Action:
					fmt.Println("Python program has started")
				default:
					fmt.Println("Python program has restarted")
			}
		} else {
			answerChan <- byteData
		}
	}
}

type PipeResponseStruct struct {
	Str string `json:"str"`
}

func writer(requestString string) {
	byteResponseData, err := json.Marshal(&PipeResponseStruct{Str: requestString})
	if err != nil {
		fmt.Println(err.Error())
		answerChan <- []byte("String error")
	}

	err = os.WriteFile(pipeOut, byteResponseData, 0)
	if err != nil {
		fmt.Println(err.Error())
		answerChan <- []byte("Program error")
	}
}

type RequestStruct struct {
	Str string `json:"str"`
}


func handler(w http.ResponseWriter, r *http.Request) {
	var requestData RequestStruct
	err := json.NewDecoder(r.Body).Decode(&requestData)
	if err != nil {

		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte("Bad request"))

	} else {

		_ = r.Body.Close()
		writer(requestData.Str)
		w.Header().Set("Content-type", "application/json; charset=utf-8")
		_, _ = w.Write(<- answerChan)

	}
}

func main() {

	err := syscall.Mkfifo(pipeIn, 0666)
	if err == syscall.EEXIST {

		err = os.Remove(pipeIn)
		if err != nil {
			fmt.Println(err.Error())
		}
		err = syscall.Mkfifo(pipeIn, 0666)
		if err != nil {
			fmt.Println(err.Error())
		}

	} else if err != nil {
		fmt.Println(err.Error())
	}

	go listener()

	select {
		case <- startChan:
			mux := http.NewServeMux()
			mux.HandleFunc("/", handler)
			fmt.Println("> Mux error:", http.ListenAndServe(listenAddr, mux).Error())
	}
}
