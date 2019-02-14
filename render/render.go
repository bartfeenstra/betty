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
		err := RenderPerson(outputDirectoryPath, &person)
		if err != nil {
			return err
		}
	}
	for _, event := range ancestry.Events {
		err := RenderEvent(outputDirectoryPath, &event)
		if err != nil {
			return err
		}
	}
	for _, place := range ancestry.Places {
		err := RenderPlace(outputDirectoryPath, &place)
		if err != nil {
			return err
		}
	}
	for _, family := range ancestry.Families {
		err := RenderFamily(outputDirectoryPath, &family)
		if err != nil {
			return err
		}
	}
	return nil
}

func RenderPerson(outputDirectoryPath string, person *gramps.Person) error {
	f, err := CreateFile(filepath.Join(outputDirectoryPath, "person", person.ID))
	if err != nil {
		return err
	}
	_, err = f.WriteString(fmt.Sprintf("%s, %s", person.FamilyName, person.IndividualName))
	if err != nil {
		return err
	}

	return nil
}

func RenderEvent(outputDirectoryPath string, event *gramps.Event) error {
	f, err := CreateFile(filepath.Join(outputDirectoryPath, "event", event.ID))
	if err != nil {
		return err
	}
	_, err = f.WriteString(event.ID)
	if err != nil {
		return err
	}

	return nil
}

func RenderPlace(outputDirectoryPath string, place *gramps.Place) error {
	f, err := CreateFile(filepath.Join(outputDirectoryPath, "place", place.ID))
	if err != nil {
		return err
	}
	_, err = f.WriteString(place.ID)
	if err != nil {
		return err
	}

	return nil
}

func RenderFamily(outputDirectoryPath string, family *gramps.Family) error {
	f, err := CreateFile(filepath.Join(outputDirectoryPath, "family", family.ID))
	if err != nil {
		return err
	}
	_, err = f.WriteString(family.ID)
	if err != nil {
		return err
	}

	return nil
}
