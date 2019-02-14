package render

import (
	"fmt"
	"github.com/bartfeenstra/betty/gramps"
	"io/ioutil"
	"os"
	"path/filepath"
)

type DirectoryNotEmpty struct {
	DirectoryPath string
}

func (err DirectoryNotEmpty) Error() string {
	return fmt.Sprintf("%s is not empty", err.DirectoryPath)
}

func AssertDirectoryIsEmpty(directoryPath string) error {
	err := CreateDirectory(directoryPath)
	if err != nil {
		return err
	}
	contents, err := ioutil.ReadDir(directoryPath)
	if err != nil {
		return err
	}
	if len(contents) > 0 {
		return DirectoryNotEmpty{
			DirectoryPath: directoryPath,
		}
	}
	return nil
}

func CreateDirectory(directoryPath string) error {
	return os.MkdirAll(directoryPath, 0740)
}

func CreateFile(directoryPath string) (*os.File, error) {
	err := CreateDirectory(directoryPath)
	if err != nil {
		return nil, err
	}
	f, err := os.Create(filepath.Join(directoryPath, "index.html"))
	if err != nil {
		return nil, err
	}
	return f, nil
}

func Render(ancestry *gramps.Ancestry, outputDirectoryPath string) error {
	err := AssertDirectoryIsEmpty(outputDirectoryPath)
	if err != nil {
		return err
	}
	for _, person := range ancestry.People {
		err := RenderEntity(outputDirectoryPath, &person)
		if err != nil {
			return err
		}
	}
	for _, event := range ancestry.Events {
		err := RenderEntity(outputDirectoryPath, &event)
		if err != nil {
			return err
		}
	}
	for _, place := range ancestry.Places {
		err := RenderEntity(outputDirectoryPath, &place)
		if err != nil {
			return err
		}
	}
	for _, family := range ancestry.Families {
		err := RenderEntity(outputDirectoryPath, &family)
		if err != nil {
			return err
		}
	}
	return nil
}

func RenderEntity(outputDirectoryPath string, entity gramps.Entity) error {
	f, err := CreateFile(filepath.Join(outputDirectoryPath, entity.GetTypeName(), entity.GetID()))
	if err != nil {
		return err
	}
	_, err = f.WriteString(entity.GetID())
	if err != nil {
		return err
	}

	return nil
}
