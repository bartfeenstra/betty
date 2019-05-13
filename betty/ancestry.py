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

    def add(self, *values):
        for value in values:
            self._add_one(value)

    def _add_one(self, value):
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
        for value in set(self._values):
            self.remove(value)
        for value in values:
            self.add(value)

    def __iter__(self):
        return self._values.__iter__()

    def __len__(self):
        return len(self._values)


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
    def complete(self) -> bool:
        return self._year is not None and self._month is not None and self._day is not None

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
        self._documents = EventHandlingSet(lambda document: document.entities.add(self),
                                           lambda document: document.entities.remove(self))

    @property
    def id(self) -> str:
        return self._id

    @property
    def documents(self) -> Iterable:
        return self._documents

    @documents.setter
    def documents(self, documents: Iterable):
        self._documents.replace(documents)


class Document(Entity):
    def __init__(self, entity_id: str, file: File):
        Entity.__init__(self, entity_id)
        self._file = file
        self._description = None
        self._notes = []
        self._entities = EventHandlingSet(lambda entity: entity.documents.add(self),
                                          lambda entity: entity.documents.remove(self))

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

    @property
    def entities(self) -> Iterable:
        return self._entities

    @entities.setter
    def entities(self, entities: Iterable):
        self._entities.replace(entities)


class Place(Entity):
    def __init__(self, entity_id: str, name: str):
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
    def name(self) -> str:
        return self._name

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
        BAPTISM = 'baptism'
        DEATH = 'death'
        BURIAL = 'burial'
        MARRIAGE = 'marriage'

    def __init__(self, entity_id: str, entity_type: Type):
        Entity.__init__(self, entity_id)
        self._date = None
        self._place = None
        self._type = entity_type
        self._people = EventHandlingSet(lambda person: person.events.add(self),
                                        lambda person: person.events.remove(self))

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
        self._parents = EventHandlingSet(lambda parent: parent.children.add(self),
                                         lambda parent: parent.children.remove(self))
        self._children = EventHandlingSet(lambda child: child.parents.add(self),
                                          lambda child: child.parents.remove(self))
        self._private = None

    @property
    def individual_name(self) -> Optional[str]:
        return self._individual_name

    @individual_name.setter
    def individual_name(self, name: str):
        self._individual_name = name

    @property
    def family_name(self) -> Optional[str]:
        return self._family_name

    @family_name.setter
    def family_name(self, name: str):
        self._family_name = name

    @property
    def names(self) -> Tuple[str, str]:
        return self._family_name or '', self._individual_name or ''

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
    def parents(self) -> Iterable:
        return self._parents

    @parents.setter
    def parents(self, parents: Iterable):
        self._parents.replace(parents)

    @property
    def children(self) -> Iterable:
        return self._children

    @children.setter
    def children(self, children: Iterable):
        self._children.replace(children)

    @property
    def siblings(self):
        siblings = set()
        for parent in self._parents:
            for sibling in parent.children:
                if sibling != self:
                    siblings.add(sibling)
        return siblings

    @property
    def private(self) -> Optional[bool]:
        return self._private

    @private.setter
    def private(self, private: Optional[bool]):
        self._private = private


class Ancestry:
    def __init__(self):
        self._documents = {}
        self._people = {}
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
