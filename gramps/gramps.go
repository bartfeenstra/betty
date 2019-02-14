package gramps

import (
	"encoding/xml"
	"io/ioutil"
)

type Handle string

type Event struct {
	ID      string `xml:"id,attr"`
	Changed string `xml:"change,attr"`
	Handle  Handle `xml:"handle,attr"`
}

type Person struct {
	ID             string `xml:"id,attr"`
	Changed        string `xml:"change,attr"`
	Handle         Handle `xml:"handle,attr"`
	FamilyName     string `xml:"name>surname"`
	IndividualName string `xml:"name>first"`
}

type Family struct {
	ID      string `xml:"id,attr"`
	Changed string `xml:"change,attr"`
	Handle  Handle `xml:"handle,attr"`
}

type Place struct {
	ID      string `xml:"id,attr"`
	Changed string `xml:"change,attr"`
	Handle  Handle `xml:"handle,attr"`
}

type Ancestry struct {
	People   []Person `xml:"people>person"`
	Events   []Event  `xml:"events>event"`
	Places   []Place  `xml:"places>placeobj"`
	Families []Family `xml:"families>family"`
}

func Parse(file_path string) (*Ancestry, error) {
	grampsBytes, err := ioutil.ReadFile(file_path)
	if err != nil {
		return nil, err
	}
	var ancestry Ancestry
	err = xml.Unmarshal(grampsBytes, &ancestry)
	return &ancestry, nil
}
