import calendar
import re
from enum import Enum
from functools import total_ordering
from os.path import splitext
from typing import Dict, Optional, List, Iterable


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
    def __init__(self, year: int, month: int = None, day: int = None):
        self._year = year
        self._month = month
        self._day = day

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> Optional[int]:
        return self._month

    @property
    def day(self) -> Optional[int]:
        return self._day

    @property
    def label(self) -> str:
        # All components.
        if self._year and self._month and self._day:
            return '%s %d, %d' % (calendar.month_name[self._month], self._day, self._year)
        # No year.
        if not self._year and self._month and self._day:
            return '%s %d' % (calendar.month_name[self._month], self._day)
        # No month.
        if self._year and not self._month:
            return str(self._year)
        # No day.
        if self._year and self._month and not self._day:
            return '%s, %d' % (calendar.month_name[self._month], self._year)
        return 'unknown'

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, Date):
            return (self._year, self._month, self._day) == (other._year, other._month, other._day)
        return NotImplemented

    def __lt__(self, other):
        if other is None:
            return False
        if isinstance(other, Date):
            return (self._year, self._month, self._day) < (other._year, other._month, other._day)
        return NotImplemented


class Coordinates:
    COORDINATE_PATTERN = r'^-?\d+(\.\d+)?$'
    INVALID_COORDINATE_MESSAGE = '"%s" is not a valid coordinate.'

    def __init__(self, latitude: str, longitude: str):
        if not re.fullmatch(self.COORDINATE_PATTERN, latitude):
            raise ValueError(self.INVALID_COORDINATE_MESSAGE % latitude)
        if not re.fullmatch(self.COORDINATE_PATTERN, longitude):
            raise ValueError(self.INVALID_COORDINATE_MESSAGE % longitude)
        self._latitude = latitude
        self._longitude = longitude

    @property
    def latitude(self) -> str:
        return self._latitude

    @property
    def longitude(self) -> str:
        return self._longitude


class Note:
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self):
        return self._text


class File:
    def __init__(self, path: str):
        self._path = path
        self._description = None
        self._type = None

    @property
    def path(self):
        return self._path

    @property
    def type(self) -> Optional[str]:
        return self._type

    @property
    def extension(self):
        return splitext(self._path)[1][1:]

    @type.setter
    def type(self, file_type: str):
        self._type = file_type

    @property
    def description(self) -> Optional[str]:
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description


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
    def __init__(self, entity_id: str, file: File, description: str):
        Entity.__init__(self, entity_id)
        self._file = file
        self._description = description
        self._notes = []

    @property
    def label(self):
        return self._description

    @property
    def file(self) -> File:
        return self._file

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
        self._events = set()

    @property
    def label(self) -> str:
        return self._name or 'unknown'

    @property
    def coordinates(self) -> Coordinates:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Coordinates):
        self._coordinates = coordinates

    @property
    def events(self):
        return self._events


class Event(Entity):
    class Type(Enum):
        BIRTH = 'birth'
        DEATH = 'death'
        MARRIAGE = 'marriage'

    _type_labels = {
        Type.BIRTH: 'Birth',
        Type.DEATH: 'Death',
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
            people_labels = [person.label for person in sorted(self._people, key=lambda x: x.label)]
            label = '%s of %s' % (self._type_labels[self._type], ', '.join(people_labels))
        else:
            label = self._type_labels[self._type]
        if self._date:
            label = '%s (%s)' % (label, self._date.label)
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
    def place(self, place: Place):
        self._place = place

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: Type):
        self._type = event_type

    @property
    def people(self):
        return self._people


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
