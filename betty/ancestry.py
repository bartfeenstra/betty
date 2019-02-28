from typing import Dict


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


class Event(Entity):
    pass


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
