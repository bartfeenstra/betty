package gramps

import (
	"encoding/xml"
	"io/ioutil"
)

type Handle string

type entity struct {
	ID      string `xml:"id,attr"`
	Changed int    `xml:"change,attr"`
	Handle  Handle `xml:"handle,attr"`
}

type Entity interface {
	GetID() string
	GetChanged() int
	GetHandle() Handle
	GetTypeName() string
}

func (event Event) GetID() string {
	return event.ID
}

func (event Event) GetChanged() int {
	return event.Changed
}

func (event Event) GetHandle() Handle {
	return event.Handle
}

func (event Event) GetTypeName() string {
	return "event"
}

type Event struct {
	entity
}

type Person struct {
	entity
	FamilyName     string `xml:"name>surname"`
	IndividualName string `xml:"name>first"`
}

func (event Person) GetID() string {
	return event.ID
}

func (event Person) GetChanged() int {
	return event.Changed
}

func (event Person) GetHandle() Handle {
	return event.Handle
}

func (event Person) GetTypeName() string {
	return "person"
}

type Family struct {
	entity
}

func (event Family) GetID() string {
	return event.ID
}

func (event Family) GetChanged() int {
	return event.Changed
}

func (event Family) GetHandle() Handle {
	return event.Handle
}

func (event Family) GetTypeName() string {
	return "family"
}

type Place struct {
	entity
}

func (event Place) GetID() string {
	return event.ID
}

func (event Place) GetChanged() int {
	return event.Changed
}

func (event Place) GetHandle() Handle {
	return event.Handle
}

func (event Place) GetTypeName() string {
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
