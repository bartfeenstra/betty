from __future__ import annotations

from contextlib import suppress
from functools import total_ordering
from pathlib import Path
from typing import List, Optional, Set, Sequence, TYPE_CHECKING

from geopy import Point

from betty.locale import Localized, Datey
from betty.media_type import MediaType
from betty.model import many_to_many, Entity, one_to_many, many_to_one, many_to_one_to_many, \
    MultipleTypesEntityCollection, EntityCollection
from betty.model.event_type import EventType, StartOfLifeEventType, EndOfLifeEventType
from betty.os import PathLike


if TYPE_CHECKING:
    from betty.builtins import _


class HasPrivacy:
    private: Optional[bool]

    def __init__(self):
        super().__init__()
        self.private = None


class Dated:
    date: Optional[Datey]

    def __init__(self):
        super().__init__()
        self.date = None


@many_to_one('entity', 'notes')
class Note(Entity):
    entity: HasNotes

    def __init__(self, note_id: str, text: str):
        super().__init__(note_id)
        self._text = text

    @property
    def text(self) -> str:
        return self._text


@one_to_many('notes', 'entity')
class HasNotes:
    notes: EntityCollection[Note]

    def __init__(self):
        super().__init__()


class Described:
    description: Optional[str]

    def __init__(self):
        super().__init__()
        self.description = None


class HasMediaType:
    media_type: Optional[MediaType]

    def __init__(self):
        super().__init__()
        self.media_type = None


class Link(HasMediaType, Localized, Described):
    url: str
    relationship: Optional[str]
    label: Optional[str]

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.label = None
        self.relationship = None


class HasLinks:
    def __init__(self):
        super().__init__()
        self._links = set()

    @property
    def links(self) -> Set[Link]:
        return self._links


@many_to_many('citations', 'facts')
class HasCitations:
    citations: EntityCollection[Citation]

    def __init__(self):
        super().__init__()


@many_to_many('entities', 'files')
class File(Entity, Described, HasPrivacy, HasMediaType, HasNotes, HasCitations):
    entities: EntityCollection[HasFiles]

    def __init__(self, file_id: Optional[str], path: PathLike, media_type: Optional[MediaType] = None):
        super().__init__(file_id)
        self._path = Path(path)
        self.media_type = media_type

    @property
    def path(self) -> Path:
        return self._path


@many_to_many('files', 'entities')
class HasFiles:
    files: EntityCollection[File]

    def __init__(self):
        super().__init__()

    @property
    def associated_files(self) -> Sequence[File]:
        return self.files


@many_to_one('contained_by', 'contains')
@one_to_many('contains', 'contained_by')
@one_to_many('citations', 'source')
class Source(Entity, Dated, HasFiles, HasLinks, HasPrivacy):
    name: Optional[str]
    contained_by: Source
    contains: EntityCollection[Source]
    citations: EntityCollection[Citation]
    author: Optional[str]
    publisher: Optional[str]

    def __init__(self, source_id: Optional[str], name: Optional[str] = None):
        super().__init__(source_id)
        self.name = name
        self.author = None
        self.publisher = None


@many_to_many('facts', 'citations')
@many_to_one('source', 'citations')
class Citation(Entity, Dated, HasFiles, HasPrivacy):
    facts: EntityCollection[HasCitations]
    source: Source
    location: Optional[str]

    def __init__(self, citation_id: Optional[str], source: Source):
        super().__init__(citation_id)
        self.location = None
        self.source = source


class PlaceName(Localized, Dated):
    def __init__(self, name: str, locale: Optional[str] = None, date: Optional[Datey] = None):
        super().__init__()
        self._name = name
        self.locale = locale
        self.date = date

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented  # pragma: no cover
        return self._name == other._name and self.locale == other.locale

    def __repr__(self):
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.name, repr(self.locale))

    def __str__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name


# @todo Do we know fore sure this is flattened correctly?
@many_to_one_to_many('enclosed_by', 'encloses', 'enclosed_by', 'encloses')
class Enclosure(Entity, Dated, HasCitations):
    encloses: Place
    enclosed_by: Place

    def __init__(self, encloses: Place, enclosed_by: Place):
        super().__init__()
        self.encloses = encloses
        self.enclosed_by = enclosed_by


@one_to_many('events', 'place')
@one_to_many('enclosed_by', 'encloses')
@one_to_many('encloses', 'enclosed_by')
class Place(Entity, HasLinks):
    enclosed_by: EntityCollection[Enclosure]
    encloses: EntityCollection[Enclosure]
    events: EntityCollection[Event]

    def __init__(self, place_id: Optional[str], names: List[PlaceName]):
        super().__init__(place_id)
        self._names = names
        self._coordinates = None

    @property
    def names(self) -> List[PlaceName]:
        return self._names

    @property
    def coordinates(self) -> Optional[Point]:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates


class PresenceRole:
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @property
    def label(self) -> str:
        raise NotImplementedError


class Subject(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'subject'

    @property
    def label(self) -> str:
        return _('Subject')


class Witness(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'witness'

    @property
    def label(self) -> str:
        return _('Witness')


class Beneficiary(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'beneficiary'

    @property
    def label(self) -> str:
        return _('Beneficiary')


class Attendee(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'attendee'

    @property
    def label(self) -> str:
        return _('Attendee')


@many_to_one_to_many('presences', 'person', 'event', 'presences')
class Presence(Entity):
    person: Person
    event: Event
    role: PresenceRole

    def __init__(self, person: Person, role: PresenceRole, event: Event):
        super().__init__()
        self.person = person
        self.role = role
        self.event = event


@many_to_one('place', 'events')
@one_to_many('presences', 'event')
class Event(Entity, Dated, HasFiles, HasCitations, Described, HasPrivacy):
    place: Place
    presences: EntityCollection[Presence]

    def __init__(self, event_id: Optional[str], event_type: EventType, date: Optional[Datey] = None):
        super().__init__(event_id)
        self.date = date
        self._type = event_type

    def __repr__(self):
        return '<%s.%s(%s, date=%s)>' % (self.__class__.__module__, self.__class__.__name__, repr(self.type), repr(self.date))

    @property
    def type(self):
        return self._type

    @property
    def associated_files(self) -> Sequence[File]:
        files = [
            *self.files,
            *[file for citation in self.citations for file in citation.associated_files],
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file


@total_ordering
@many_to_one('person', 'names')
class PersonName(Entity, Localized, HasCitations):
    person: Person

    def __init__(self, person: Person, individual: Optional[str] = None, affiliation: Optional[str] = None):
        super().__init__()
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, PersonName):
            return NotImplemented  # pragma: no cover
        return (self._affiliation or '', self._individual or '') == (other._affiliation or '', other._individual or '')

    def __gt__(self, other):
        if other is None:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented  # pragma: no cover
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
class Person(Entity, HasFiles, HasCitations, HasLinks, HasPrivacy):
    parents: EntityCollection[Person]
    children: EntityCollection[Person]
    presences: EntityCollection[Presence]
    names: EntityCollection[PersonName]

    def __init__(self, person_id: Optional[str]):
        super().__init__(person_id)

    def __eq__(self, other):
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id == other.id

    def __gt__(self, other):
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id > other.id

    @property
    def name(self) -> Optional[PersonName]:
        try:
            return self._names[0]
        except IndexError:
            return None

    @property
    def alternative_names(self) -> EntityCollection[PersonName]:
        return self.names[1:]

    @property
    def start(self) -> Optional[Event]:
        with suppress(StopIteration):
            return next((presence.event for presence in self.presences if isinstance(presence.event.type, StartOfLifeEventType)))

    @property
    def end(self) -> Optional[Event]:
        with suppress(StopIteration):
            return next((presence.event for presence in self.presences if isinstance(presence.event.type, EndOfLifeEventType)))

    @property
    def siblings(self) -> List:
        siblings = []
        for parent in self._parents:
            for sibling in parent.children:
                if sibling != self and sibling not in siblings:
                    siblings.append(sibling)
        return siblings

    @property
    def associated_files(self) -> Sequence[File]:
        files = [
            *self.files,
            *[file for name in self.names for citation in name._citations for file in citation.associated_files],
            *[file for presence in self.presences for file in presence.event.associated_files]
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file


class Ancestry:
    def __init__(self):
        self._entities = MultipleTypesEntityCollection()

    @property
    def entities(self) -> MultipleTypesEntityCollection:
        return self._entities
