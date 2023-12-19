from __future__ import annotations

from contextlib import suppress
from enum import Enum
from functools import total_ordering
from pathlib import Path
from reprlib import recursive_repr
from typing import Iterable, Any

from geopy import Point

from betty.classtools import repr_instance
from betty.locale import Localized, Datey, Str, Localizable
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
    def __init__(
        self,
        *args: Any,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if [privacy, public, private].count(None) < 2:
            raise ValueError(f'Only one of the `privacy`, `public`, and `private` arguments to {type(self)}.__init__() may be given at a time.')
        if privacy is not None:
            self._privacy = privacy
        elif public is True:
            self._privacy = Privacy.PUBLIC
        elif private is True:
            self._privacy = Privacy.PRIVATE
        else:
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
    def __init__(
        self,
        *args: Any,
        date: Datey | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['date'] = self.date
        return dict_state, slots_state


@many_to_one('entity', 'betty.model.ancestry.HasNotes', 'notes')
class Note(HasMutablePrivacy, UserFacingEntity, Entity):
    entity: HasNotes

    def __init__(
        self,
        text: str,
        *,
        id: str | None = None,
        entity: HasNotes | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
        )
        self._text = text
        if entity is not None:
            self.entity = entity

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_text'] = self._text
        return dict_state, slots_state

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._('Note')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Notes')

    @property
    def text(self) -> str:
        return self._text

    @property
    def label(self) -> Str:
        return Str.plain(self.text)


@one_to_many('notes', 'betty.model.ancestry.Note', 'entity')
class HasNotes:
    def __init__(  # type: ignore[misc]
        self: HasNotes & Entity,
        *args: Any,
        notes: Iterable[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if notes is not None:
            self.notes = notes  # type: ignore[assignment]

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
    def __init__(
        self,
        *args: Any,
        description: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['description'] = self.description
        return dict_state, slots_state


class HasMediaType(Pickleable):
    def __init__(
        self,
        *args: Any,
        media_type: MediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['media_type'] = self.media_type
        return dict_state, slots_state


class Link(HasMediaType, Localized, Described):
    url: str
    relationship: str | None
    label: str | None

    def __init__(
        self,
        url: str,
        *,
        relationship: str | None = None,
        label: str | None = None,
        description: str | None = None,
        media_type: MediaType | None = None,
        locale: str | None = None,
    ):
        super().__init__(
            media_type=media_type,
            description=description,
            locale=locale,
        )
        self.url = url
        self.label = label
        self.relationship = relationship

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['url'] = self.url
        dict_state['relationship'] = self.relationship
        dict_state['label'] = self.label
        return dict_state, slots_state


class HasLinks(Pickleable):
    def __init__(
        self,
        *args: Any,
        links: set[Link] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._links: set[Link] = set() if links is None else links

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
        citations: Iterable[Citation] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if citations is not None:
            self.citations = citations  # type: ignore[assignment]

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
        path: Path,
        *,
        id: str | None = None,
        media_type: MediaType | None = None,
        description: str | None = None,
        notes: Iterable[Note] | None = None,
        citations: Iterable[Citation] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            media_type=media_type,
            description=description,
            notes=notes,
            citations=citations,
            privacy=privacy,
            public=public,
            private=private,
        )
        self._path = path

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
    def entity_type_label(cls) -> Str:
        return Str._('File')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Files')

    @property
    def path(self) -> Path:
        return self._path

    @property
    def label(self) -> Str:
        return Str.plain(self.description) if self.description else super().label


@many_to_many('files', 'betty.model.ancestry.File', 'entities')
class HasFiles:
    def __init__(  # type: ignore[misc]
        self: HasFiles & Entity,
        *args: Any,
        files: Iterable[File] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if files is not None:
            self.files = files  # type: ignore[assignment]

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
    contained_by: Source | None

    def __init__(
        self,
        name: str | None = None,
        *,
        id: str | None = None,
        author: str | None = None,
        publisher: str | None = None,
        contained_by: Source | None = None,
        contains: Iterable[Source] | None = None,
        date: Datey | None = None,
        files: Iterable[File] | None = None,
        links: set[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            date=date,
            files=files,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        self.name = name
        self.author = author
        self.publisher = publisher
        if contained_by is not None:
            self.contained_by = contained_by
        if contains is not None:
            self.contains = contains  # type: ignore[assignment]

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
    def entity_type_label(cls) -> Str:
        return Str._('Source')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Sources')

    @property
    def label(self) -> Str:
        return Str.plain(self.name) if self.name else super().label


class AnonymousSource(Source):
    @property  # type: ignore[override]
    def name(self) -> str:
        return 'private'

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
    def __init__(
        self,
        *,
        id: str | None = None,
        facts: Iterable[HasCitations] | None = None,
        source: Source | None = None,
        location: Str | None = None,
        date: Datey | None = None,
        files: Iterable[File] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            date=date,
            files=files,
            privacy=privacy,
            public=public,
            private=private,
        )
        if facts is not None:
            self.facts = facts  # type: ignore[assignment]
        self.location = location
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
    def entity_type_label(cls) -> Str:
        return Str._('Citation')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Citations')

    @property
    def label(self) -> Str:
        return self.location or Str.plain('')


class AnonymousCitation(Citation):
    @property  # type: ignore[override]
    def location(self) -> Str:
        return Str._("private (in order to protect people's privacy)")

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
        *,
        locale: str | None = None,
        date: Datey | None = None,
    ):
        super().__init__(
            date=date,
            locale=locale,
        )
        self._name = name

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
    ):
        super().__init__()
        self.encloses = encloses
        self.enclosed_by = enclosed_by

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._('Enclosure')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Enclosures')


@one_to_many('events', 'betty.model.ancestry.Event', 'place')
@one_to_many('enclosed_by', 'betty.model.ancestry.Enclosure', 'encloses')
@one_to_many('encloses', 'betty.model.ancestry.Enclosure', 'enclosed_by')
class Place(HasLinks, UserFacingEntity, Entity):
    def __init__(
        self,
        *,
        id: str | None = None,
        names: list[PlaceName] | None = None,
        events: Iterable[Event] | None = None,
        coordinates: Point | None = None,
        links: set[Link] | None = None,
    ):
        super().__init__(
            id,
            links=links,
        )
        self._names = [] if names is None else names
        self._coordinates = coordinates
        if events is not None:
            self.events = events  # type: ignore[assignment]

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
    def entity_type_label(cls) -> Str:
        return Str._('Place')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Places')

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
    def label(self) -> Str:
        # @todo Negotiate this by locale and date.
        with suppress(IndexError):
            return Str.plain(self.names[0].name)
        return super().label


class PresenceRole:
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @property
    def label(self) -> Str:
        raise NotImplementedError(repr(self))


class Subject(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'subject'

    @property
    def label(self) -> Str:
        return Str._('Subject')


class Witness(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'witness'

    @property
    def label(self) -> Str:
        return Str._('Witness')


class Beneficiary(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'beneficiary'

    @property
    def label(self) -> Str:
        return Str._('Beneficiary')


class Attendee(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'attendee'

    @property
    def label(self) -> Str:
        return Str._('Attendee')


class Speaker(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'speaker'

    @property
    def label(self) -> Str:
        return Str._('Speaker')


class Celebrant(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'celebrant'

    @property
    def label(self) -> Str:
        return Str._('Celebrant')


class Organizer(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'organizer'

    @property
    def label(self) -> Str:
        return Str._('Organizer')


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
        person: Person | None,
        role: PresenceRole,
        event: Event | None,
    ):
        super().__init__(None)
        self.person = person
        self.role = role
        self.event = event

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['role'] = self.role
        return dict_state, slots_state

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._('Presence')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Presences')

    def _get_privacy(self) -> Privacy:
        return merge_privacies(self.person, self.event)


@many_to_one('place', 'betty.model.ancestry.Place', 'events')
@one_to_many('presences', 'betty.model.ancestry.Presence', 'event')
class Event(Dated, HasFiles, HasCitations, Described, HasMutablePrivacy, UserFacingEntity, Entity):
    place: Place | None

    def __init__(
        self,
        *,
        id: str | None = None,
        event_type: type[EventType],
        date: Datey | None = None,
        files: Iterable[File] | None = None,
        citations: Iterable[Citation] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place: Place | None = None,
        description: str | None = None,
    ):
        super().__init__(
            id,
            date=date,
            files=files,
            citations=citations,
            privacy=privacy,
            public=public,
            private=private,
            description=description,
        )
        self._event_type = event_type
        if place is not None:
            self.place = place

    @property
    def label(self) -> Str:
        format_kwargs: dict[str, str | Localizable] = {
            'event_type': self._event_type.label(),
        }
        subjects = [
            presence.person
            for presence
            in self.presences
            if presence.public and isinstance(presence.role, Subject) and presence.person is not None and presence.person.public
        ]
        if subjects:
            format_kwargs['subjects'] = Str.call(lambda localizer: ', '.join(person.label.localize(localizer) for person in subjects))
        if self.description is not None:
            format_kwargs['event_description'] = self.description

        if subjects:
            if self.description is None:
                return Str._('{event_type} of {subjects}', **format_kwargs)
            else:
                return Str._('{event_type} ({event_description}) of {subjects}', **format_kwargs)
        if self.description is None:
            return Str._('{event_type}', **format_kwargs)
        else:
            return Str._('{event_type} ({event_description})', **format_kwargs)

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
    def entity_type_label(cls) -> Str:
        return Str._('Event')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Events')

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
        *,
        id: str | None = None,
        person: Person | None = None,
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        if not individual and not affiliation:
            raise ValueError('The individual and affiliation names must not both be empty.')
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
        )
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
    def entity_type_label(cls) -> Str:
        return Str._('Person name')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('Person names')

    @property
    def individual(self) -> str | None:
        return self._individual

    @property
    def affiliation(self) -> str | None:
        return self._affiliation

    @property
    def label(self) -> Str:
        if self.private:
            return Str._('private')
        return Str._(
            '{individual_name} {affiliation_name}',
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
        *,
        id: str | None = None,
        files: Iterable[File] | None = None,
        citations: Iterable[Citation] | None = None,
        links: set[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        parents: Iterable[Person] | None = None,
        children: Iterable[Person] | None = None,
    ):
        super().__init__(
            id,
            files=files,
            citations=citations,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        if children is not None:
            self.children = children  # type: ignore[assignment]
        if parents is not None:
            self.parents = parents  # type: ignore[assignment]

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
    def entity_type_label(cls) -> Str:
        return Str._('Person')

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._('People')

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
    def label(self) -> Str:
        return self.name.label if self.name else super().label


class Ancestry(MultipleTypesEntityCollection[Entity]):
    def __init__(self):
        super().__init__()
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
