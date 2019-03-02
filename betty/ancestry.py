import calendar
import re
from enum import Enum
from typing import Dict, Optional, List


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
        if self._year and self._month and self._day:
            return '%s %d, %d' % (calendar.month_name[self._month], self._day, self._year)
        if not self._year and self._month and self._day:
            return '%s %d' % (calendar.month_name[self._month], self._day)
        if self._year and self._month and not self._day:
            return '%s, %d' % (calendar.month_name[self._month], self._year)
        return 'unknown'


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


class Entity:
    def __init__(self, entity_id):
        self._id = entity_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self.id


class Place(Entity):
    def __init__(self, entity_id: str, name: str = None):
        Entity.__init__(self, entity_id)
        self._name = name
        self._coordinates = None

    @property
    def label(self) -> str:
        return self._name or 'unknown'

    @property
    def coordinates(self) -> Coordinates:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Coordinates):
        self._coordinates = coordinates


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

    @property
    def label(self) -> str:
        type_label = self._type_labels[self._type]
        if self._date:
            return '%s (%s)' % (type_label, self._date.label)
        return type_label

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


class Person(Entity):
    def __init__(self, entity_id: str, individual_name: str = None, family_name: str = None):
        Entity.__init__(self, entity_id)
        self._individual_name = individual_name
        self._family_name = family_name
        self._birth = None
        self._death = None
        self._descendant_family = None
        self._ancestor_families = []

    @property
    def label(self) -> str:
        return '%s, %s' % (self._family_name or 'unknown', self._individual_name or 'unknown')

    @property
    def birth(self) -> Event:
        return self._birth

    @birth.setter
    def birth(self, birth: Event):
        self._birth = birth

    @property
    def death(self) -> Event:
        return self._death

    @death.setter
    def death(self, death: Event):
        self._death = death

    @property
    def descendant_family(self):
        return self._descendant_family

    @descendant_family.setter
    def descendant_family(self, family):
        self._descendant_family = family

    @property
    def ancestor_families(self):
        return self._ancestor_families

    @ancestor_families.setter
    def ancestor_families(self, families):
        self._ancestor_families = families

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
        self._parents = []
        self._children = []

    @property
    def parents(self) -> List[Person]:
        return self._parents

    @parents.setter
    def parents(self, parents: List[Person]):
        self._parents = parents

    @property
    def children(self) -> List[Person]:
        return self._children

    @children.setter
    def children(self, children: List[Person]):
        self._children = children


class Ancestry:
    def __init__(self):
        self._people = {}
        self._families = {}
        self._places = {}
        self._events = {}

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
