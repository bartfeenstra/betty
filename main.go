package main

import (
	"fmt"
	"github.com/bartfeenstra/betty/gramps"
	"github.com/jessevdk/go-flags"
	"os"
)

type Options struct {
	FilePath string `long:"filepath" required:"true"`
}

func ExitBetty(err error) {
	fmt.Println(err)
	os.Exit(3)
}

func main() {
	options := Options{}
	parser := flags.NewParser(&options, flags.None)
	_, err := parser.Parse()
	if err != nil {
		ExitBetty(err)
	}
	ancestry, err := gramps.Parse(options.FilePath)
	if err != nil {
		ExitBetty(err)
	}
	fmt.Printf("%#v", ancestry)
}
