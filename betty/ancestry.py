import calendar
from enum import Enum
from typing import Dict, Optional


class Entity:
    def __init__(self, entity_id):
        self._id = entity_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self.id


class Person(Entity):
    def __init__(self, entity_id: str, individual_name: str = None, family_name: str = None):
        Entity.__init__(self, entity_id)
        self._individual_name = individual_name
        self._family_name = family_name

    @property
    def label(self) -> str:
        return '%s, %s' % (self._family_name or 'unknown', self._individual_name or 'unknown')


class Family(Entity):
    pass


class Place(Entity):
    def __init__(self, entity_id: str, name: str = None):
        Entity.__init__(self, entity_id)
        self._name = name

    @property
    def label(self) -> str:
        return self._name or 'unknown'


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
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: Type):
        self._type = event_type


class Ancestry:
    def __init__(self, people=None, families=None, places=None, events=None):
        self._people = people or {}
        self._families = families or {}
        self._places = places or {}
        self._events = events or {}

    @property
    def people(self) -> Dict[str, Person]:
        return self._people

    @property
    def families(self) -> Dict[str, Family]:
        return self._families

    @property
    def places(self) -> Dict[str, Place]:
        return self._places

    @property
    def events(self) -> Dict[str, Event]:
        return self._events
