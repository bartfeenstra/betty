package gramps

import (
	"encoding/xml"
	"io/ioutil"
)

type Handle string

type entity struct {
	Id      string `xml:"id,attr"`
	Changed int    `xml:"change,attr"`
	Handle  Handle `xml:"handle,attr"`
}

type Entity interface {
	GetId() string
	GetChanged() int
	GetHandle() Handle
	GetTypeName() string
	GetLabel() string
}

func (entity entity) GetId() string {
	return entity.Id
}

func (entity entity) GetChanged() int {
	return entity.Changed
}

func (entity entity) GetHandle() Handle {
	return entity.Handle
}

func (entity entity) GetLabel() string {
	return entity.GetId()
}

type Event struct {
	entity
}

func (_ Event) GetTypeName() string {
	return "event"
}

type Person struct {
	entity
	FamilyName     string `xml:"name>surname"`
	IndividualName string `xml:"name>first"`
}

func (_ Person) GetTypeName() string {
	return "person"
}

func (person Person) GetLabel() string {
	return person.FamilyName + ", " + person.IndividualName
}

type Family struct {
	entity
}

func (_ Family) GetTypeName() string {
	return "family"
}

type Place struct {
	entity
}

func (_ Place) GetTypeName() string {
	return "place"
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
