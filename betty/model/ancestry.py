from __future__ import annotations

import builtins
from contextlib import suppress
from enum import Enum
from functools import total_ordering
from pathlib import Path
from reprlib import recursive_repr
from typing import Iterable, Any

from geopy import Point

from betty.classtools import repr_instance
from betty.locale import Localized, Datey, Localizer, Localizable
from betty.media_type import MediaType
from betty.model import many_to_many, Entity, one_to_many, many_to_one, many_to_one_to_many, \
    MultipleTypesEntityCollection, EntityCollection, UserFacingEntity, EntityTypeAssociationRegistry, \
    PickleableEntityGraph
from betty.model.event_type import EventType, StartOfLifeEventType, EndOfLifeEventType
from betty.pickle import State, Pickleable


class Privacy(Enum):
    PUBLIC = 1
    PRIVATE = 2
    UNDETERMINED = 3


class HasPrivacy(Pickleable):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._privacy = Privacy.UNDETERMINED

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_privacy'] = self._privacy
        return dict_state, slots_state

    def _get_privacy(self) -> Privacy:
        return self._privacy

    @property
    def privacy(self) -> Privacy:
        return self._get_privacy()

    @property
    def private(self) -> bool:
        return self._get_privacy() is Privacy.PRIVATE

    @property
    def public(self) -> bool:
        # Undetermined privacy defaults to public.
        return self._get_privacy() is not Privacy.PRIVATE


class HasMutablePrivacy(HasPrivacy):
    @property
    def privacy(self) -> Privacy:
        return self._get_privacy()

    @privacy.setter
    def privacy(self, privacy: Privacy) -> None:
        self._privacy = privacy

    @privacy.deleter
    def privacy(self) -> None:
        self._privacy = Privacy.UNDETERMINED

    @property
    def private(self) -> bool:
        return self._get_privacy() is Privacy.PRIVATE

    @private.setter
    def private(self, private: True) -> None:
        self._privacy = Privacy.PRIVATE

    @property
    def public(self) -> bool:
        # Undetermined privacy defaults to public.
        return self._get_privacy() is not Privacy.PRIVATE

    @public.setter
    def public(self, public: True) -> None:
        self._privacy = Privacy.PUBLIC


def is_private(target: Any) -> bool:
    if isinstance(target, HasPrivacy):
        return target.private
    return False


def is_public(target: Any) -> bool:
    if isinstance(target, HasPrivacy):
        return target.public
    return True


def resolve_privacy(privacy: Privacy | HasPrivacy | None) -> Privacy:
    if privacy is None:
        return Privacy.UNDETERMINED
    if isinstance(privacy, Privacy):
        return privacy
    return privacy.privacy


def merge_privacies(*privacies: Privacy | HasPrivacy | None) -> Privacy:
    privacies = {
        resolve_privacy(privacy)
        for privacy
        in privacies
    }
    if Privacy.PRIVATE in privacies:
        return Privacy.PRIVATE
    if Privacy.UNDETERMINED in privacies:
        return Privacy.UNDETERMINED
    return Privacy.PUBLIC


class Dated(Pickleable):
    date: Datey | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.date = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['date'] = self.date
        return dict_state, slots_state


@many_to_one('entity', 'betty.model.ancestry.HasNotes', 'notes')
class Note(HasMutablePrivacy, UserFacingEntity, Entity):
    entity: HasNotes

    def __init__(self, note_id: str | None, text: str):
        super().__init__(note_id)
        self._text = text

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_text'] = self._text
        return dict_state, slots_state

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


@one_to_many('notes', 'betty.model.ancestry.Note', 'entity')
class HasNotes:
    def __init__(  # type: ignore[misc]
        self: HasNotes & Entity,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )

    @property
    def notes(self) -> EntityCollection[Note]:  # type: ignore[empty-body]
        pass

    @notes.setter
    def notes(self, notes: Iterable[Note]) -> None:
        pass

    @notes.deleter
    def notes(self) -> None:
        pass


class Described(Pickleable):
    description: str | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.description = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['description'] = self.description
        return dict_state, slots_state


class HasMediaType(Pickleable):
    media_type: MediaType | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.media_type = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['media_type'] = self.media_type
        return dict_state, slots_state


class Link(HasMediaType, Localized, Described):
    url: str
    relationship: str | None
    label: str | None

    def __init__(self, url: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.url = url
        self.label = None
        self.relationship = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['url'] = self.url
        dict_state['relationship'] = self.relationship
        dict_state['label'] = self.label
        return dict_state, slots_state


class HasLinks(Pickleable):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._links = set[Link]()

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_links'] = self._links
        return dict_state, slots_state

    @property
    def links(self) -> set[Link]:
        return self._links


@many_to_many('citations', 'betty.model.ancestry.Citation', 'facts')
class HasCitations:
    def __init__(  # type: ignore[misc]
        self: HasCitations & Entity,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore[empty-body]
        pass

    @citations.setter
    def citations(self, citations: Iterable[Citation]) -> None:
        pass

    @citations.deleter
    def citations(self) -> None:
        pass


@many_to_many('entities', 'betty.model.ancestry.HasFiles', 'files')
class File(Described, HasMutablePrivacy, HasMediaType, HasNotes, HasCitations, UserFacingEntity, Entity):
    def __init__(
        self,
        file_id: str | None,
        path: Path,
        media_type: MediaType | None = None,
        *,
        localizer: Localizer | None = None
    ):
        super().__init__(file_id, localizer=localizer)
        self._path = path
        self.media_type = media_type

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_path'] = self._path
        return dict_state, slots_state

    @property
    def entities(self) -> EntityCollection[Entity]:  # type: ignore[empty-body]
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
        return self.description if self.description else super().label


@many_to_many('files', 'betty.model.ancestry.File', 'entities')
class HasFiles:
    def __init__(  # type: ignore[misc]
        self: HasFiles & Entity,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )

    @property
    def files(self) -> EntityCollection[File]:  # type: ignore[empty-body]
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


@many_to_one('contained_by', 'betty.model.ancestry.Source', 'contains')
@one_to_many('contains', 'betty.model.ancestry.Source', 'contained_by')
@one_to_many('citations', 'betty.model.ancestry.Citation', 'source')
class Source(Dated, HasFiles, HasLinks, HasMutablePrivacy, UserFacingEntity, Entity):
    name: str | None
    contained_by: Source | None
    author: str | None
    publisher: str | None

    def __init__(
        self,
        source_id: str | None,
        name: str | None = None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(source_id, localizer=localizer)
        self.name = name
        self.author = None
        self.publisher = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['name'] = self.name
        dict_state['author'] = self.author
        dict_state['publisher'] = self.publisher
        return dict_state, slots_state

    def _get_privacy(self) -> Privacy:
        privacy = super()._get_privacy()
        if self.contained_by:
            return merge_privacies(privacy, self.contained_by.privacy)
        return privacy

    @property
    def contains(self) -> EntityCollection[Source]:  # type: ignore[empty-body]
        pass

    @contains.setter
    def contains(self, contains: Iterable[Source]) -> None:
        pass

    @contains.deleter
    def contains(self) -> None:
        pass

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore[empty-body]
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
        return self.name if self.name else super().label


class AnonymousSource(Source):
    @property  # type: ignore[override]
    def name(self) -> str:
        return self.localizer._('private')

    @name.setter
    def name(self, _) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass

    @name.deleter
    def name(self) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass


@many_to_many('facts', 'betty.model.ancestry.HasCitations', 'citations')
@many_to_one('source', 'betty.model.ancestry.Source', 'citations')
class Citation(Dated, HasFiles, HasMutablePrivacy, UserFacingEntity, Entity):
    source: Source | None
    location: str | None

    def __init__(
        self,
        citation_id: str | None,
        source: Source | None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(citation_id, localizer=localizer)
        self.location = None
        self.source = source

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['location'] = self.location
        return dict_state, slots_state

    def _get_privacy(self) -> Privacy:
        privacy = super()._get_privacy()
        if self.source:
            return merge_privacies(privacy, self.source.privacy)
        return privacy

    @property
    def facts(self) -> EntityCollection[HasCitations & Entity]:  # type: ignore[empty-body]
        pass

    @facts.setter
    def facts(self, facts: Iterable[HasCitations & Entity]) -> None:
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

    @property
    def label(self) -> str:
        return self.location or super().label


class AnonymousCitation(Citation):
    @property  # type: ignore[override]
    def location(self) -> str:
        return self.localizer._("private (in order to protect people's privacy)")

    @location.setter
    def location(self, _) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass

    @location.deleter
    def location(self) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass


class PlaceName(Localized, Dated):
    def __init__(
        self,
        name: str,
        locale: str | None = None,
        date: Datey | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._name = name
        self.locale = locale
        self.date = date

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_name'] = self._name
        return dict_state, slots_state

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented  # pragma: no cover
        return self._name == other._name and self.locale == other.locale

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, name=self.name, locale=self.locale)

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name


@many_to_one_to_many(
    'betty.model.ancestry.Place',
    'enclosed_by',
    'encloses',
    'enclosed_by',
    'betty.model.ancestry.Place',
    'encloses',
)
class Enclosure(Dated, HasCitations, Entity):
    encloses: Place | None
    enclosed_by: Place | None

    def __init__(
        self,
        encloses: Place | None,
        enclosed_by: Place | None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(localizer=localizer)
        self.encloses = encloses
        self.enclosed_by = enclosed_by

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Enclosure')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Enclosures')


@one_to_many('events', 'betty.model.ancestry.Event', 'place')
@one_to_many('enclosed_by', 'betty.model.ancestry.Enclosure', 'encloses')
@one_to_many('encloses', 'betty.model.ancestry.Enclosure', 'enclosed_by')
class Place(HasLinks, UserFacingEntity, Entity):
    def __init__(
        self,
        place_id: str | None,
        names: list[PlaceName],
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(place_id, localizer=localizer)
        self._names = names
        self._coordinates = None

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_names'] = self._names
        dict_state['_coordinates'] = self._coordinates
        return dict_state, slots_state

    @property
    def enclosed_by(self) -> EntityCollection[Enclosure]:  # type: ignore[empty-body]
        pass

    @enclosed_by.setter
    def enclosed_by(self, enclosed_by: Iterable[Enclosure]) -> None:
        pass

    @enclosed_by.deleter
    def enclosed_by(self) -> None:
        pass

    @property
    def encloses(self) -> EntityCollection[Enclosure]:  # type: ignore[empty-body]
        pass

    @encloses.setter
    def encloses(self, encloses: Iterable[Enclosure]) -> None:
        pass

    @encloses.deleter
    def encloses(self) -> None:
        pass

    @property
    def events(self) -> EntityCollection[Event]:  # type: ignore[empty-body]
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
    def names(self) -> list[PlaceName]:
        return self._names

    @property
    def coordinates(self) -> Point | None:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @property
    def label(self) -> str:
        # @todo Negotiate this by locale and date.
        with suppress(IndexError):
            return self.names[0].name
        return super().label


class PresenceRole(Localizable):
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @property
    def label(self) -> str:
        raise NotImplementedError(repr(self))


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


class Speaker(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'speaker'

    @property
    def label(self) -> str:
        return self.localizer._('Speaker')


class Celebrant(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'celebrant'

    @property
    def label(self) -> str:
        return self.localizer._('Celebrant')


class Organizer(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'organizer'

    @property
    def label(self) -> str:
        return self.localizer._('Organizer')


@many_to_one_to_many(
    'betty.model.ancestry.Person',
    'presences',
    'person',
    'event',
    'betty.model.ancestry.Event',
    'presences',
)
class Presence(HasPrivacy, Entity):
    person: Person | None
    event: Event | None
    role: PresenceRole

    def __init__(
        self,
        presence_id: str | None,
        person: Person | None,
        role: PresenceRole,
        event: Event | None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(presence_id, localizer=localizer)
        self.person = person
        self.role = role
        self.event = event

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['role'] = self.role
        return dict_state, slots_state

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Presence')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Presences')

    def _get_privacy(self) -> Privacy:
        return merge_privacies(self.person, self.event)


@many_to_one('place', 'betty.model.ancestry.Place', 'events')
@one_to_many('presences', 'betty.model.ancestry.Presence', 'event')
class Event(Dated, HasFiles, HasCitations, Described, HasMutablePrivacy, UserFacingEntity, Entity):
    place: Place | None

    @property
    def label(self) -> str:
        label = self.event_type.label(self.localizer)
        if self.description is not None:
            label += f' ({self.description})'
        subjects = [
            presence.person
            for presence
            in self.presences
            if presence.public and isinstance(presence.role, Subject) and presence.person is not None and presence.person.public
        ]
        if subjects:
            return self.localizer._('{event_type} of {subjects}').format(
                event_type=label,
                subjects=', '.join(person.label for person in subjects),
            )
        return label

    def __init__(
        self,
        event_id: str | None,
        event_type: builtins.type[EventType],
        date: Datey | None = None,
        *,
        localizer: Localizer | None = None
    ):
        super().__init__(event_id, localizer=localizer)
        self.date = date
        self._event_type = event_type

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_event_type'] = self._event_type
        return dict_state, slots_state

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, id=self._id, type=self._event_type)

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore[empty-body]
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

    @property
    def event_type(self) -> type[EventType]:
        return self._event_type

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
@many_to_one('person', 'betty.model.ancestry.Person', 'names')
class PersonName(Localized, HasCitations, HasMutablePrivacy, Entity):
    person: Person | None

    def __init__(
        self,
        person_name_id: str | None,
        person: Person | None,
        individual: str | None = None,
        affiliation: str | None = None,
        *,
        localizer: Localizer | None = None
    ):
        if not individual and not affiliation:
            raise ValueError('The individual and affiliation names must not both be empty.')
        super().__init__(person_name_id, localizer=localizer)
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_individual'] = self._individual
        dict_state['_affiliation'] = self._affiliation
        return dict_state, slots_state

    def _get_privacy(self) -> Privacy:
        privacy = super()._get_privacy()
        if self.person:
            return merge_privacies(privacy, self.person.privacy)
        return privacy

    def __repr__(self) -> str:
        return repr_instance(self, id=self.id, individual=self.individual, affiliation=self.affiliation)

    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        return (self._individual or '') == (other._individual or '') and (self._affiliation or '') == (other._affiliation or '')

    def __gt__(self, other: Any) -> bool:
        if other is None:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self._individual or '') > (other._individual or '') and (self._affiliation or '') > (other._affiliation or '')

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Person name')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Person names')

    @property
    def individual(self) -> str | None:
        return self._individual

    @property
    def affiliation(self) -> str | None:
        return self._affiliation

    @property
    def label(self) -> str:
        if self.private:
            return self.localizer._('private')
        return self.localizer._('{individual_name} {affiliation_name}').format(
            individual_name='…' if not self.individual else self.individual,
            affiliation_name='…' if not self.affiliation else self.affiliation,
        )


@total_ordering
@many_to_many('parents', 'betty.model.ancestry.Person', 'children')
@many_to_many('children', 'betty.model.ancestry.Person', 'parents')
@one_to_many('presences', 'betty.model.ancestry.Presence', 'person')
@one_to_many('names', 'betty.model.ancestry.PersonName', 'person')
class Person(HasFiles, HasCitations, HasLinks, HasMutablePrivacy, UserFacingEntity, Entity):
    def __init__(
        self,
        person_id: str | None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(person_id, localizer=localizer)

    @property
    def parents(self) -> EntityCollection[Person]:  # type: ignore[empty-body]
        pass

    @parents.setter
    def parents(self, parents: Iterable[Person]) -> None:
        pass

    @parents.deleter
    def parents(self) -> None:
        pass

    @property
    def children(self) -> EntityCollection[Person]:  # type: ignore[empty-body]
        pass

    @children.setter
    def children(self, children: Iterable[Person]) -> None:
        pass

    @children.deleter
    def children(self) -> None:
        pass

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore[empty-body]
        pass

    @presences.setter
    def presences(self, presences: Iterable[Presence]) -> None:
        pass

    @presences.deleter
    def presences(self) -> None:
        pass

    @property
    def names(self) -> EntityCollection[PersonName]:  # type: ignore[empty-body]
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
        return super().__eq__(other) and self.name == other.name

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Person):
            return NotImplemented
        if self.name is None and other.name is None:
            return False
        return self.name > other.name  # type: ignore[operator]

    @property
    def name(self) -> PersonName | None:
        try:
            return next(filter(is_public, self.names))
        except StopIteration:
            try:
                return self.names[0]
            except IndexError:
                return None

    @property
    def alternative_names(self) -> list[PersonName]:
        return [
            name
            for name
            in self.names
            if is_public(name)
        ][1:]

    def _shortcut_event(self, event_type: type[EventType]) -> Presence | None:
        for presence in self.presences:
            if not isinstance(presence.role, Subject):
                continue
            if presence.event is None:
                continue
            if not issubclass(presence.event.event_type, event_type):
                continue
            if not presence.public:
                continue
            return presence
        return None

    @property
    def start(self) -> Presence | None:
        return self._shortcut_event(StartOfLifeEventType)

    @property
    def end(self) -> Presence | None:
        return self._shortcut_event(EndOfLifeEventType)

    @property
    def siblings(self) -> list[Person]:
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
            *[
                file
                for name
                in self.names
                for citation
                in name.citations
                for file
                in citation.associated_files
            ],
            *[
                file
                for presence
                in self.presences
                if presence.event is not None
                for file
                in presence.event.associated_files
            ]
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
        return self.name.label if self.name else super().label


class Ancestry(MultipleTypesEntityCollection[Entity]):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._check_graph = True

    def __getstate__(self) -> PickleableEntityGraph:
        return PickleableEntityGraph(*self)

    def __setstate__(self, state: PickleableEntityGraph) -> None:
        self._collections = {}
        self.add_unchecked_graph(*state.build())

    def add_unchecked_graph(self, *entities: Entity) -> None:
        self._check_graph = False
        try:
            self.add(*entities)
        finally:
            self._check_graph = True

    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in EntityTypeAssociationRegistry.get_all_associations(entity):
                for associate in EntityTypeAssociationRegistry.get_associates(entity, association):
                    yield associate
