from __future__ import annotations

from contextlib import suppress
import copy
from functools import total_ordering
from pathlib import Path
from typing import Optional, Set, List, Dict, Iterable, Any, Type

from geopy import Point

from betty.locale import Localized, Datey, Localizer, Localizable
from betty.media_type import MediaType
from betty.model import many_to_many, Entity, one_to_many, many_to_one, many_to_one_to_many, \
    MultipleTypesEntityCollection, EntityCollection, UserFacingEntity, EntityVariation, FlattenedEntityCollection
from betty.model.event_type import EventType, StartOfLifeEventType, EndOfLifeEventType


class HasPrivacy:
    private: Optional[bool]

    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasPrivacy)
        super().__init__(*args, **kwargs)
        self.private = None


class Dated:
    date: Optional[Datey]

    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, Dated)
        super().__init__(*args, **kwargs)
        self.date = None


@many_to_one('entity', 'notes')
class Note(UserFacingEntity, Entity):
    entity: HasNotes

    def __init__(self, note_id: str | None, text: str):
        super().__init__(note_id)
        self._text = text

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Note')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Notes')

    @property
    def text(self) -> str:
        return self._text

    @property
    def label(self) -> str:
        return self.text


@one_to_many('notes', 'entity')
class HasNotes(EntityVariation):
    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasNotes)
        super().__init__(*args, **kwargs)

    @property
    def notes(self) -> EntityCollection[Note]:  # type: ignore
        pass

    @notes.setter
    def notes(self, notes: Iterable[Note]) -> None:
        pass

    @notes.deleter
    def notes(self) -> None:
        pass


class Described:
    description: Optional[str]

    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, Described)
        super().__init__(*args, **kwargs)
        self.description = None


class HasMediaType:
    media_type: Optional[MediaType]

    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasMediaType)
        super().__init__(*args, **kwargs)
        self.media_type = None


class Link(HasMediaType, Localized, Described):
    url: str
    relationship: Optional[str]
    label: Optional[str]

    def __init__(self, url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.label = None
        self.relationship = None


class HasLinks:
    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasLinks)
        super().__init__(*args, **kwargs)
        self._links = set()

    @property
    def links(self) -> Set[Link]:
        return self._links


@many_to_many('citations', 'facts')
class HasCitations(EntityVariation):
    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasCitations)
        super().__init__(*args, **kwargs)

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore
        pass

    @citations.setter
    def citations(self, citations: Iterable[Citation]) -> None:
        pass

    @citations.deleter
    def citations(self) -> None:
        pass


@many_to_many('entities', 'files')
class File(Described, HasPrivacy, HasMediaType, HasNotes, HasCitations, UserFacingEntity, Entity):
    def __init__(self, file_id: Optional[str], path: Path, media_type: Optional[MediaType] = None, *args, **kwargs):
        super().__init__(file_id, *args, **kwargs)
        self._path = path
        self.media_type = media_type

    @property
    def entities(self) -> EntityCollection[Entity]:  # type: ignore
        pass

    @entities.setter
    def entities(self, entities: Iterable[Entity]) -> None:
        pass

    @entities.deleter
    def entities(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('File')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Files')

    @property
    def path(self) -> Path:
        return self._path

    @property
    def label(self) -> str:
        return self._default_label() if self.description is None else self.description


@many_to_many('files', 'entities')
class HasFiles(EntityVariation):
    def __init__(self, *args, **kwargs):
        assert issubclass(self.__class__, HasFiles)
        super().__init__(*args, **kwargs)

    @property
    def files(self) -> EntityCollection[File]:  # type: ignore
        pass

    @files.setter
    def files(self, files: Iterable[File]) -> None:
        pass

    @files.deleter
    def files(self) -> None:
        pass

    @property
    def associated_files(self) -> Iterable[File]:
        return self.files


@many_to_one('contained_by', 'contains')
@one_to_many('contains', 'contained_by')
@one_to_many('citations', 'source')
class Source(Dated, HasFiles, HasLinks, HasPrivacy, UserFacingEntity, Entity):
    name: Optional[str]
    contained_by: Source
    author: Optional[str]
    publisher: Optional[str]

    def __init__(self, source_id: Optional[str], name: Optional[str] = None, *, localizer: Localizer | None = None):
        super().__init__(source_id, localizer=localizer)
        self.name = name
        self.author = None
        self.publisher = None

    @property
    def contains(self) -> EntityCollection[Source]:  # type: ignore
        pass

    @contains.setter
    def contains(self, contains: Iterable[Source]) -> None:
        pass

    @contains.deleter
    def contains(self) -> None:
        pass

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore
        pass

    @citations.setter
    def citations(self, citations: Iterable[Citation]) -> None:
        pass

    @citations.deleter
    def citations(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Source')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Sources')

    @property
    def label(self) -> str:
        return self._default_label() if not self.name else self.name


@many_to_many('facts', 'citations')
@many_to_one('source', 'citations')
class Citation(Dated, HasFiles, HasPrivacy, UserFacingEntity, Entity):
    source: Source
    location: Optional[str]

    def __init__(self, citation_id: Optional[str], source: Optional[Source], *, localizer: Localizer | None = None):
        super().__init__(citation_id, localizer=localizer)
        self.location = None
        self.source = source  # type: ignore

    @property
    def facts(self) -> EntityCollection[HasCitations]:  # type: ignore
        pass

    @facts.setter
    def facts(self, facts: Iterable[HasCitations]) -> None:
        pass

    @facts.deleter
    def facts(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Citation')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Citations')


class PlaceName(Localized, Dated):
    def __init__(self, name: str, locale: Optional[str] = None, date: Optional[Datey] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        self.locale = locale
        self.date = date

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented  # pragma: no cover
        return self._name == other._name and self.locale == other.locale

    def __repr__(self) -> str:
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.name, repr(self.locale))

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name


@many_to_one_to_many('enclosed_by', 'encloses', 'enclosed_by', 'encloses')
class Enclosure(Dated, HasCitations, Entity):
    encloses: Place
    enclosed_by: Place

    def __init__(self, encloses: Optional[Place], enclosed_by: Optional[Place], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encloses = encloses  # type: ignore
        self.enclosed_by = enclosed_by  # type: ignore


@one_to_many('events', 'place')
@one_to_many('enclosed_by', 'encloses')
@one_to_many('encloses', 'enclosed_by')
class Place(HasLinks, UserFacingEntity, Entity):
    def __init__(self, place_id: Optional[str], names: List[PlaceName], *args, **kwargs):
        super().__init__(place_id, *args, **kwargs)
        self._names = names
        self._coordinates = None

    @property
    def enclosed_by(self) -> EntityCollection[Enclosure]:  # type: ignore
        pass

    @enclosed_by.setter
    def enclosed_by(self, enclosed_by: Iterable[Enclosure]) -> None:
        pass

    @enclosed_by.deleter
    def enclosed_by(self) -> None:
        pass

    @property
    def encloses(self) -> EntityCollection[Enclosure]:  # type: ignore
        pass

    @encloses.setter
    def encloses(self, encloses: Iterable[Enclosure]) -> None:
        pass

    @encloses.deleter
    def encloses(self) -> None:
        pass

    @property
    def events(self) -> EntityCollection[Event]:  # type: ignore
        pass

    @events.setter
    def events(self, events: Iterable[Event]) -> None:
        pass

    @events.deleter
    def events(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Place')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Places')

    @property
    def names(self) -> List[PlaceName]:
        return self._names

    @property
    def coordinates(self) -> Optional[Point]:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @property
    def label(self) -> str:
        # @todo Negotiate this by locale and date.
        with suppress(IndexError):
            return self.names[0].name
        return self._default_label()


class PresenceRole(Localizable):
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
        return self.localizer._('Subject')


class Witness(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'witness'

    @property
    def label(self) -> str:
        return self.localizer._('Witness')


class Beneficiary(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'beneficiary'

    @property
    def label(self) -> str:
        return self.localizer._('Beneficiary')


class Attendee(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'attendee'

    @property
    def label(self) -> str:
        return self.localizer._('Attendee')


@many_to_one_to_many('presences', 'person', 'event', 'presences')
class Presence(Entity):
    person: Person
    event: Event
    role: PresenceRole

    def __init__(self, person: Optional[Person], role: PresenceRole, event: Optional[Event], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person  # type: ignore
        self.role = role
        self.event = event  # type: ignore


@many_to_one('place', 'events')
@one_to_many('presences', 'event')
class Event(Dated, HasFiles, HasCitations, Described, HasPrivacy, UserFacingEntity, Entity):
    place: Optional[Place]

    def __init__(self, event_id: Optional[str], event_type: Type[EventType], date: Optional[Datey] = None, *args, **kwargs):
        super().__init__(event_id, *args, **kwargs)
        self.date = date
        self._type = event_type

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore
        pass

    @presences.setter
    def presences(self, presences: Iterable[Presence]) -> None:
        pass

    @presences.deleter
    def presences(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Event')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Events')

    def __repr__(self) -> str:
        return '<%s.%s(%s, date=%s)>' % (self.__class__.__module__, self.__class__.__name__, repr(self.type), repr(self.date))

    @property
    def type(self) -> Type[EventType]:
        return self._type

    @property
    def associated_files(self) -> Iterable[File]:
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
class PersonName(Localized, HasCitations, Entity):
    person: Person

    def __init__(self, person: Optional[Person], individual: Optional[str] = None, affiliation: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not individual and not affiliation:
            raise ValueError('The individual and affiliation names must not both be empty.')
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person  # type: ignore

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Person name')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Person names')

    def __repr__(self) -> str:
        return '<%s.%s(%s, %s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.individual, self.affiliation, repr(self.person))

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return False
        if not isinstance(other, PersonName):
            return NotImplemented  # pragma: no cover
        return (self._affiliation or '', self._individual or '') == (other._affiliation or '', other._individual or '')

    def __gt__(self, other: Any) -> bool:
        if other is None:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented  # pragma: no cover
        return (self._affiliation or '', self._individual or '') > (other._affiliation or '', other._individual or '')

    @property
    def individual(self) -> Optional[str]:
        return self._individual

    @property
    def affiliation(self) -> Optional[str]:
        return self._affiliation

    @property
    def label(self) -> str:
        return self.localizer._('{individual_name} {affiliation_name}').format(
            individual_name='…' if not self.individual else self.individual,
            affiliation_name='…' if not self.affiliation else self.affiliation,
        )


@total_ordering
@many_to_many('parents', 'children')
@many_to_many('children', 'parents')
@one_to_many('presences', 'person')
@one_to_many('names', 'person')
class Person(HasFiles, HasCitations, HasLinks, HasPrivacy, UserFacingEntity, Entity):
    def __init__(self, person_id: Optional[str], *args, **kwargs):
        super().__init__(person_id, *args, **kwargs)

    @property
    def parents(self) -> EntityCollection[Person]:  # type: ignore
        pass

    @parents.setter
    def parents(self, parents: Iterable[Person]) -> None:
        pass

    @parents.deleter
    def parents(self) -> None:
        pass

    @property
    def children(self) -> EntityCollection[Person]:  # type: ignore
        pass

    @children.setter
    def children(self, children: Iterable[Person]) -> None:
        pass

    @children.deleter
    def children(self) -> None:
        pass

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore
        pass

    @presences.setter
    def presences(self, presences: Iterable[Presence]) -> None:
        pass

    @presences.deleter
    def presences(self) -> None:
        pass

    @property
    def names(self) -> EntityCollection[PersonName]:  # type: ignore
        pass

    @names.setter
    def names(self, names: Iterable[PersonName]) -> None:
        pass

    @names.deleter
    def names(self) -> None:
        pass

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Person')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('People')

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id == other.id

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id > other.id

    @property
    def name(self) -> Optional[PersonName]:
        try:
            return self.names[0]
        except IndexError:
            return None

    @property
    def alternative_names(self) -> EntityCollection[PersonName]:
        return self.names[1:]

    @property
    def start(self) -> Optional[Event]:
        with suppress(StopIteration):
            return next((presence.event for presence in self.presences if issubclass(presence.event.type, StartOfLifeEventType)))
        return None

    @property
    def end(self) -> Optional[Event]:
        with suppress(StopIteration):
            return next((presence.event for presence in self.presences if issubclass(presence.event.type, EndOfLifeEventType)))
        return None

    @property
    def siblings(self) -> List[Person]:
        siblings = []
        for parent in self.parents:
            for sibling in parent.children:
                if sibling != self and sibling not in siblings:
                    siblings.append(sibling)
        return siblings

    @property
    def associated_files(self) -> Iterable[File]:
        files = [
            *self.files,
            *[file for name in self.names for citation in name.citations for file in citation.associated_files],
            *[file for presence in self.presences for file in presence.event.associated_files]
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file

    @property
    def label(self) -> str:
        return self.name.label if self.name else self._default_label()


class Ancestry(Localizable):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._entities = MultipleTypesEntityCollection(localizer=localizer)

    def __copy__(self) -> Ancestry:
        copied = self.__class__()
        copied.entities.append(*self.entities)
        return copied

    def __deepcopy__(self, memo: Dict) -> Ancestry:
        copied = self.__class__()
        copied.entities.append(*[copy.deepcopy(entity, memo) for entity in self.entities])
        return copied

    def __getstate__(self) -> FlattenedEntityCollection:
        entities = FlattenedEntityCollection()
        entities.add_entity(*self.entities)

        return entities

    def __setstate__(self, state: FlattenedEntityCollection):
        self._entities = MultipleTypesEntityCollection()
        self._entities.append(*state.unflatten())

    def _on_localizer_change(self) -> None:
        self._entities.localizer = self.localizer

    @property
    def entities(self) -> MultipleTypesEntityCollection:
        return self._entities
