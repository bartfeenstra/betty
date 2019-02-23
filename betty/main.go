package betty

import (
	"fmt"
	"github.com/bartfeenstra/betty/betty/gramps"
	"github.com/bartfeenstra/betty/betty/render"
	"github.com/jessevdk/go-flags"
	"os"
)

type Options struct {
	InputFilePath       string `short:"i" long:"input" required:"true" description:"The path to the Gramps XML file to render."`
	OutputDirectoryPath string `short:"o" long:"output" required:"true" description:"The path to the output directory."`
}

func ExitBetty(err error) {
	fmt.Println(err)
	os.Exit(3)
}

func main() {
	options := Options{}
	parser := flags.NewParser(&options, flags.HelpFlag)
	_, err := parser.Parse()
	if err != nil {
		ExitBetty(err)
	}
	ancestry, err := gramps.Parse(options.InputFilePath)
	if err != nil {
		ExitBetty(err)
	}
	err = render.Render(ancestry, options.OutputDirectoryPath)
	if err != nil {
		ExitBetty(err)
	}
	fmt.Printf("The genealogy data from %s has been rendered and placed into %s.\n", options.InputFilePath, options.OutputDirectoryPath)
}
