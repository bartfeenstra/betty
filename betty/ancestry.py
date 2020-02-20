from enum import Enum
from functools import total_ordering
from os.path import splitext, basename
from typing import Dict, Optional, List, Iterable, Set, Union, TypeVar, Generic, Callable

from geopy import Point

from betty.locale import Localized, Datey

T = TypeVar('T')


class EventHandlingSetList(Generic[T]):
    def __init__(self, addition_handler: Callable[[T], None], removal_handler: Callable[[T], None]):
        self._values = []
        self._addition_handler = addition_handler
        self._removal_handler = removal_handler

    @property
    def list(self) -> List:
        return list(self._values)

    def prepend(self, *values):
        for value in reversed(values):
            if value in self._values:
                return
            self._values.insert(0, value)
            self._addition_handler(value)

    def append(self, *values):
        for value in values:
            if value in self._values:
                return
            self._values.append(value)
            self._addition_handler(value)

    def remove(self, value):
        if value not in self._values:
            return
        self._values.remove(value)
        self._removal_handler(value)

    def replace(self, values: Iterable):
        for value in list(self._values):
            self.remove(value)
        for value in values:
            self.append(value)

    def clear(self) -> None:
        self.replace([])

    def __iter__(self):
        return self._values.__iter__()

    def __len__(self):
        return len(self._values)


ManyAssociation = Union[EventHandlingSetList[T], Iterable]


class _to_many:
    def __init__(self, self_name: str, associated_name: str):
        self._self_name = self_name
        self._associated_name = associated_name

    def __call__(self, cls):
        _decorated_self_name = '_%s' % self._self_name
        original_init = cls.__init__

        def _init(decorated_self, *args, **kwargs):
            association = EventHandlingSetList(self._create_addition_handler(decorated_self),
                                               self._create_removal_handler(decorated_self))
            setattr(decorated_self, _decorated_self_name, association)
            original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init
        setattr(cls, self._self_name, property(
            lambda decorated_self: getattr(decorated_self, _decorated_self_name),
            lambda decorated_self, values: getattr(decorated_self, _decorated_self_name).replace(values),
            lambda decorated_self: getattr(decorated_self, _decorated_self_name).clear(),
        ))
        return cls

    def _create_addition_handler(self, decorated_self):
        raise NotImplementedError

    def _create_removal_handler(self, decorated_self):
        raise NotImplementedError


class many_to_many(_to_many):
    def _create_addition_handler(self, decorated_self):
        return lambda associated: getattr(associated, self._associated_name).append(decorated_self)

    def _create_removal_handler(self, decorated_self):
        return lambda associated: getattr(associated, self._associated_name).remove(decorated_self)


class one_to_many(_to_many):
    def _create_addition_handler(self, decorated_self):
        return lambda associated: setattr(associated, self._associated_name, decorated_self)

    def _create_removal_handler(self, decorated_self):
        return lambda associated: setattr(associated, self._associated_name, None)


def many_to_one(self_name: str, associated_name: str):
    def decorator(cls):
        _decorated_self_name = '_%s' % self_name
        original_init = cls.__init__

        def _init(decorated_self, *args, **kwargs):
            setattr(decorated_self, _decorated_self_name, None)
            original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init

        def _set(decorated_self, value):
            previous_value = getattr(decorated_self, _decorated_self_name)
            setattr(decorated_self, _decorated_self_name, value)
            if previous_value is not None:
                getattr(previous_value, associated_name).remove(decorated_self)
            if value is not None:
                getattr(value, associated_name).append(decorated_self)
        setattr(cls, self_name, property(
            lambda self: getattr(self, _decorated_self_name),
            _set,
            lambda self: setattr(self, _decorated_self_name, None),
        ))
        return cls
    return decorator


class Dated:
    def __init__(self):
        self._date = None

    @property
    def date(self) -> Optional[Datey]:
        return self._date

    @date.setter
    def date(self, date: Datey):
        self._date = date


class Note:
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self):
        return self._text


class Identifiable:
    def __init__(self, id: str):
        self._id = id

    @property
    def id(self) -> str:
        return self._id


class Described:
    def __init__(self):
        self._description = None

    @property
    def description(self) -> Optional[str]:
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description


class Link:
    def __init__(self, url: str, label: Optional[str] = None):
        self._url = url
        self._label = label

    @property
    def url(self) -> str:
        return self._url

    @property
    def label(self) -> str:
        return self._label if self._label else self._url


class HasLinks:
    def __init__(self):
        self._links = set()

    @property
    def links(self) -> Set[Link]:
        return self._links


@many_to_many('entities', 'files')
class File(Identifiable, Described):
    entities: ManyAssociation

    def __init__(self, file_id: str, path: str):
        Identifiable.__init__(self, file_id)
        Described.__init__(self)
        self._path = path
        self._type = None
        self._notes = []

    @property
    def path(self) -> str:
        return self._path

    @property
    def type(self) -> Optional[str]:
        return self._type

    @type.setter
    def type(self, file_type: str):
        self._type = file_type

    @property
    def name(self) -> str:
        return basename(self._path)

    @property
    def basename(self) -> str:
        return splitext(self._path)[0]

    @property
    def extension(self) -> Optional[str]:
        extension = splitext(self._path)[1][1:]
        return extension if extension else None

    @property
    def notes(self) -> List[Note]:
        return self._notes

    @notes.setter
    def notes(self, notes: List[Note]):
        self._notes = notes

    @property
    def sources(self) -> Iterable['Source']:
        for entity in self.entities:
            if isinstance(entity, Source):
                yield entity
            if isinstance(entity, Citation):
                yield entity.source

    @property
    def citations(self) -> Iterable['Citation']:
        for entity in self.entities:
            if isinstance(entity, Citation):
                yield entity


@many_to_many('files', 'entities')
class HasFiles:
    files: ManyAssociation[File]


@many_to_one('contained_by', 'contains')
@one_to_many('contains', 'contained_by')
@one_to_many('citations', 'source')
class Source(Identifiable, Dated, HasFiles, HasLinks):
    def __init__(self, source_id: str, name: str):
        Identifiable.__init__(self, source_id)
        Dated.__init__(self)
        HasFiles.__init__(self)
        HasLinks.__init__(self)
        self._name = name
        self._author = None
        self._publisher = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: str):
        self._author = author

    @property
    def publisher(self) -> Optional[str]:
        return self._publisher

    @publisher.setter
    def publisher(self, publisher: str):
        self._publisher = publisher


@many_to_many('facts', 'citations')
@many_to_one('source', 'citations')
class Citation(Identifiable, Dated, HasFiles):
    source: Source

    def __init__(self, citation_id: str, source: Source):
        Identifiable.__init__(self, citation_id)
        Dated.__init__(self)
        HasFiles.__init__(self)
        self._location = None
        self.source = source

    @property
    def location(self) -> Optional[str]:
        return self._location

    @location.setter
    def location(self, location: str):
        self._location = location


@many_to_many('citations', 'facts')
class HasCitations:
    citations: ManyAssociation[Citation]


class LocalizedName(Localized):
    def __init__(self, name: str, locale: Optional[str] = None):
        Localized.__init__(self)
        self._name = name
        self.locale = locale

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._name == other._name and self._locale == other._locale

    def __repr__(self):
        return '%s(%s, %s)' % (type(self).__name__, self._name, self._locale.__repr__())

    def __str__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name


@one_to_many('events', 'place')
@many_to_one('enclosed_by', 'encloses')
@one_to_many('encloses', 'enclosed_by')
class Place(Identifiable, HasLinks):
    def __init__(self, place_id: str, names: List[LocalizedName]):
        Identifiable.__init__(self, place_id)
        HasLinks.__init__(self)
        self._names = names
        self._coordinates = None

    @property
    def names(self) -> List[LocalizedName]:
        return self._names

    @property
    def coordinates(self) -> Point:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates


@many_to_one('person', 'presences')
@many_to_one('event', 'presences')
class Presence:
    person: Optional['Person']
    event: Optional['Event']

    class Role(Enum):
        SUBJECT = 'subject'
        WITNESS = 'witness'
        ATTENDEE = 'attendee'

    def __init__(self, role: Role):
        self._role = role
        self._person = None
        self._event = None

    @property
    def role(self) -> 'Role':
        return self._role


@many_to_one('place', 'events')
@one_to_many('presences', 'event')
class Event(Dated, HasFiles, HasCitations, Described):
    place: Place
    presences: ManyAssociation[Presence]

    class Type(Enum):
        BIRTH = 'birth'
        BAPTISM = 'baptism'
        ADOPTION = 'adoption'
        CREMATION = 'cremation'
        DEATH = 'death'
        BURIAL = 'burial'
        ENGAGEMENT = 'engagement'
        MARRIAGE = 'marriage'
        MARRIAGE_BANNS = 'marriage-banns'
        DIVORCE = 'divorce'
        DIVORCE_FILING = 'divorce-filing'
        RESIDENCE = 'residence'
        IMMIGRATION = 'immigration'
        EMIGRATION = 'emigration'
        OCCUPATION = 'occupation'
        RETIREMENT = 'retirement'

    def __init__(self, event_type: Type, date: Optional[Datey] = None, place: Optional[Place] = None):
        Dated.__init__(self)
        HasFiles.__init__(self)
        HasCitations.__init__(self)
        Described.__init__(self)
        self._date = date
        self._type = event_type

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, event_type: Type):
        self._type = event_type


class IdentifiableEvent(Event, Identifiable):
    def __init__(self, event_id: str, *args, **kwargs):
        Identifiable.__init__(self, event_id)
        Event.__init__(self, *args, **kwargs)


@total_ordering
@many_to_one('person', 'names')
class PersonName(Localized, HasCitations):
    person: Optional['Person']

    def __init__(self, individual: Optional[str] = None, affiliation: Optional[str] = None):
        Localized.__init__(self)
        HasCitations.__init__(self)
        self._individual = individual
        self._affiliation = affiliation

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self._affiliation or '', self._individual or '') == (other._affiliation or '', other._individual or '')

    def __gt__(self, other):
        if other is None:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self._affiliation or '', self._individual or '') > (other._affiliation or '', other._individual or '')

    @property
    def individual(self) -> str:
        return self._individual

    @property
    def affiliation(self) -> str:
        return self._affiliation


@total_ordering
@many_to_many('parents', 'children')
@many_to_many('children', 'parents')
@one_to_many('presences', 'person')
@one_to_many('names', 'person')
class Person(Identifiable, HasFiles, HasCitations, HasLinks):
    parents: ManyAssociation['Person']
    children: ManyAssociation['Person']
    presences: ManyAssociation[Presence]
    names: ManyAssociation[PersonName]

    def __init__(self, person_id: str):
        Identifiable.__init__(self, person_id)
        HasFiles.__init__(self)
        HasCitations.__init__(self)
        HasLinks.__init__(self)
        self._private = None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id == other.id

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id > other.id

    @property
    def name(self) -> Optional[PersonName]:
        try:
            return self._names.list[0]
        except IndexError:
            return None

    @property
    def alternative_names(self) -> List[PersonName]:
        return self._names.list[1:]

    @property
    def start(self) -> Optional[Event]:
        for event_type in [Event.Type.BIRTH, Event.Type.BAPTISM]:
            for presence in self.presences:
                if presence.event.type == event_type and presence.role == Presence.Role.SUBJECT:
                    return presence.event
        return None

    @property
    def end(self) -> Optional[Event]:
        for event_type in [Event.Type.DEATH, Event.Type.BURIAL]:
            for presence in self.presences:
                if presence.event.type == event_type and presence.role == Presence.Role.SUBJECT:
                    return presence.event
        return None

    @property
    def siblings(self) -> List:
        siblings = []
        for parent in self._parents:
            for sibling in parent.children:
                if sibling != self and sibling not in siblings:
                    siblings.append(sibling)
        return siblings

    @property
    def private(self) -> Optional[bool]:
        return self._private

    @private.setter
    def private(self, private: Optional[bool]):
        self._private = private


class Ancestry:
    def __init__(self):
        self._files = {}
        self._people = {}
        self._places = {}
        self._events = {}
        self._sources = {}
        self._citations = {}

    @property
    def files(self) -> Dict[str, File]:
        return self._files

    @files.setter
    def files(self, files: Dict[str, File]):
        self._files = files

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
    def events(self) -> Dict[str, IdentifiableEvent]:
        return self._events

    @events.setter
    def events(self, events: Dict[str, Event]):
        self._events = events

    @property
    def sources(self) -> Dict[str, Source]:
        return self._sources

    @sources.setter
    def sources(self, sources: Dict[str, Source]):
        self._sources = sources

    @property
    def citations(self) -> Dict[str, Citation]:
        return self._citations

    @citations.setter
    def citations(self, citations: Dict[str, Citation]):
        self._citations = citations
