from enum import Enum
from functools import total_ordering
from os.path import splitext
from typing import Dict, Optional, List, Iterable, Tuple

from geopy import Point


class EventHandlingSet:
    def __init__(self, addition_handler=None, removal_handler=None):
        self._values = set()
        self._addition_handler = addition_handler
        self._removal_handler = removal_handler

    def add(self, value):
        if value in self._values:
            return
        self._values.add(value)
        if self._addition_handler is not None:
            self._addition_handler(value)

    def remove(self, value):
        if value not in self._values:
            return
        self._values.remove(value)
        if self._removal_handler is not None:
            self._removal_handler(value)

    def replace(self, values: Iterable):
        self._values = set(values)

    def __iter__(self):
        return self._values.__iter__()


@total_ordering
class Date:
    def __init__(self, year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None):
        self._year = year
        self._month = month
        self._day = day

    @property
    def year(self) -> Optional[int]:
        return self._year

    @property
    def month(self) -> Optional[int]:
        return self._month

    @property
    def day(self) -> Optional[int]:
        return self._day

    @property
    def parts(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        return self._year, self._month, self._day

    def __eq__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts

    def __lt__(self, other):
        if not isinstance(other, Date):
            return NotImplemented
        if None in self.parts or None in other.parts:
            return NotImplemented
        return self.parts < other.parts


class Note:
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self):
        return self._text


class File:
    def __init__(self, path: str):
        self._path = path
        self._type = None

    @property
    def path(self):
        return self._path

    @property
    def extension(self) -> Optional[str]:
        extension = splitext(self._path)[1][1:]
        return extension if extension else None


class Entity:
    def __init__(self, entity_id: str):
        self._id = entity_id
        self._documents = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self.id

    @property
    def documents(self) -> List:
        return self._documents

    @documents.setter
    def documents(self, documents: List):
        self._documents = documents


class Document(Entity):
    def __init__(self, entity_id: str, file: File):
        Entity.__init__(self, entity_id)
        self._file = file
        self._description = None
        self._notes = []

    @property
    def label(self):
        return self._description if self._description else ''

    @property
    def file(self) -> File:
        return self._file

    @property
    def description(self) -> Optional[str]:
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description

    @property
    def notes(self) -> List[Note]:
        return self._notes

    @notes.setter
    def notes(self, notes: List[Note]):
        self._notes = notes


class Place(Entity):
    def __init__(self, entity_id: str, name: str = None):
        Entity.__init__(self, entity_id)
        self._name = name
        self._coordinates = None

        def handle_event_addition(event: Event):
            event.place = self

        def handle_event_removal(event: Event):
            event.place = None

        self._events = EventHandlingSet(
            handle_event_addition, handle_event_removal)
        self._enclosed_by = None

        def handle_encloses_addition(place):
            place.enclosed_by = self

        def handle_encloses_removal(place):
            place.enclosed_by = None

        self._encloses = EventHandlingSet(
            handle_encloses_addition, handle_encloses_removal)

    @property
    def label(self) -> str:
        return self._name or 'unknown'

    @property
    def coordinates(self) -> Point:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @property
    def events(self) -> Iterable:
        return self._events

    @property
    def enclosed_by(self):
        return self._enclosed_by

    @enclosed_by.setter
    def enclosed_by(self, place):
        previous_place = self._enclosed_by
        self._enclosed_by = place
        if previous_place is not None:
            previous_place.encloses.remove(self)
        if place is not None:
            place.encloses.add(self)

    @property
    def encloses(self) -> Iterable:
        return self._encloses


class Event(Entity):
    class Type(Enum):
        BIRTH = 'birth'
        DEATH = 'death'
        BURIAL = 'burial'
        MARRIAGE = 'marriage'

    _type_labels = {
        Type.BIRTH: 'Birth',
        Type.DEATH: 'Death',
        Type.BURIAL: 'Burial',
        Type.MARRIAGE: 'Marriage',
    }

    def __init__(self, entity_id: str, entity_type: Type):
        Entity.__init__(self, entity_id)
        self._date = None
        self._place = None
        self._type = entity_type
        self._people = EventHandlingSet(lambda person: person.events.add(self),
                                        lambda person: person.events.remove(self))

    @property
    def label(self) -> str:
        people = set(self._people)
        if people:
            people_labels = [person.label for person in sorted(
                self._people, key=lambda x: x.label)]
            label = '%s of %s' % (
                self._type_labels[self._type], ' and '.join(people_labels))
        else:
            label = self._type_labels[self._type]
        return label

    @property
    def date(self) -> Optional[Date]:
        return self._date

    @date.setter
    def date(self, date: Date):
        self._date = date

    @property
    def place(self) -> Optional[Place]:
        return self._place

    @place.setter
    def place(self, place: Optional[Place]):
        previous_place = self._place
        self._place = place
        if previous_place is not None:
            previous_place.events.remove(self)
        if place is not None:
            place.events.add(self)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: Type):
        self._type = event_type

    @property
    def people(self):
        return self._people

    @people.setter
    def people(self, people):
        self._people.replace(people)


class Person(Entity):
    def __init__(self, entity_id: str, individual_name: str = None, family_name: str = None):
        Entity.__init__(self, entity_id)
        self._individual_name = individual_name
        self._family_name = family_name
        self._events = EventHandlingSet(lambda event: event.people.add(self),
                                        lambda event: event.people.remove(self))
        self._descendant_family = None
        self._ancestor_families = EventHandlingSet(lambda family: family.parents.add(self),
                                                   lambda family: family.parents.remove(self))

    @property
    def label(self) -> str:
        return '%s, %s' % (self._family_name or 'unknown', self._individual_name or 'unknown')

    @property
    def individual_name(self) -> Optional[str]:
        return self._individual_name

    @property
    def family_name(self) -> Optional[str]:
        return self._family_name

    @property
    def events(self) -> Iterable:
        return self._events

    @events.setter
    def events(self, events: Iterable):
        self._events.replace(events)

    @property
    def birth(self) -> Optional[Event]:
        for event in self._events:
            if event.type == Event.Type.BIRTH:
                return event
        return None

    @property
    def death(self) -> Optional[Event]:
        for event in self._events:
            if event.type == Event.Type.DEATH:
                return event
        return None

    @property
    def descendant_family(self):
        return self._descendant_family

    @descendant_family.setter
    def descendant_family(self, family):
        previous_family = self._descendant_family
        self._descendant_family = family
        if previous_family is not None:
            previous_family.children.remove(self)
        if family is not None:
            family.children.add(self)

    @property
    def ancestor_families(self) -> Iterable:
        return self._ancestor_families

    @ancestor_families.setter
    def ancestor_families(self, families: Iterable):
        self._ancestor_families.replace(families)

    @property
    def parents(self):
        return self._descendant_family.parents if self._descendant_family else []

    @property
    def children(self):
        children = []
        for family in self._ancestor_families:
            children += family.children
        return children

    @property
    def siblings(self):
        siblings = set()
        for parent in self.parents:
            for sibling in parent.children:
                if sibling != self:
                    siblings.add(sibling)
        return siblings


class Family(Entity):
    def __init__(self, entity_id: str):
        Entity.__init__(self, entity_id)

        def handle_child_addition(child):
            child.descendant_family = self

        def handle_child_removal(child):
            child.descendant_family = None

        self._parents = EventHandlingSet(lambda parent: parent.ancestor_families.add(self),
                                         lambda parent: parent.ancestor_families.remove(self))
        self._children = EventHandlingSet(
            handle_child_addition, handle_child_removal)

    @property
    def parents(self) -> Iterable[Person]:
        return self._parents

    @parents.setter
    def parents(self, parents: Iterable[Person]):
        self._parents.replace(parents)

    @property
    def children(self) -> Iterable[Person]:
        return self._children

    @children.setter
    def children(self, children: Iterable[Person]):
        self._children.replace(children)


class Ancestry:
    def __init__(self):
        self._documents = {}
        self._people = {}
        self._families = {}
        self._places = {}
        self._events = {}

    @property
    def documents(self) -> Dict[str, Document]:
        return self._documents

    @documents.setter
    def documents(self, documents: Dict[str, Document]):
        self._documents = documents

    @property
    def people(self) -> Dict[str, Person]:
        return self._people

    @people.setter
    def people(self, people: Dict[str, Person]):
        self._people = people

    @property
    def families(self) -> Dict[str, Family]:
        return self._families

    @families.setter
    def families(self, families: Dict[str, Family]):
        self._families = families

    @property
    def places(self) -> Dict[str, Place]:
        return self._places

    @places.setter
    def places(self, places: Dict[str, Place]):
        self._places = places

    @property
    def events(self) -> Dict[str, Event]:
        return self._events

    @events.setter
    def events(self, events: Dict[str, Event]):
        self._events = events
