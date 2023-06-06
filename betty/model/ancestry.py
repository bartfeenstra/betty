from __future__ import annotations

import copy
from contextlib import suppress
from functools import total_ordering
from pathlib import Path
from typing import Iterable, Any

from geopy import Point

from betty.app import App
from betty.locale import Localized, Datey, Localizer, Localizable, datey_schema, locale_schema
from betty.media_type import MediaType
from betty.model import many_to_many, Entity, one_to_many, many_to_one, many_to_one_to_many, UserFacingEntity, \
    MultipleTypesEntityCollection, FlattenedEntityCollection, EntityCollection, is_identifiable
from betty.model.event_type import EventType, StartOfLifeEventType, EndOfLifeEventType
from betty.serde import Describable, Schema, object_schema
from betty.serde.dump import DictDump, Dumpable, Dump, void_to_dict, minimize


def dump_coordinates(coordinates: Point, app: App) -> DictDump[Dump]:
    return {
        '@context': {
            'latitude': 'https://schema.org/latitude',
            'longitude': 'https://schema.org/longitude',
        },
        '@type': 'https://schema.org/GeoCoordinates',
        'latitude': coordinates.latitude,
        'longitude': coordinates.longitude,
    }


def coordinates_schema(app: App) -> Schema:
    return {
        'type': 'object',
        'properties': {
            'latitude': {
                'type': 'number',
            },
            'longitude': {
                'type': 'number',
            },
        },
        'required': [
            'latitude',
            'longitude',
        ],
        'additionalProperties': False,
    }


class HasPrivacy(Describable, Dumpable[DictDump[Dump]]):
    private: bool | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.private = None

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        dump['private'] = self.private
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['private'] = {  # type: ignore[index]
            'oneOf': [
                {
                    'type': 'boolean',
                },
                {
                    'type': 'null',
                }
            ]
        }
        schema['required'].append(  # type: ignore[union-attr]
            'private',
        )
        return schema


class Dated(Describable, Dumpable[DictDump[Dump]]):
    date: Datey | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.date = None

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        if self.date is not None:
            dump['date'] = self.date.dump(app)
        return minimize(dump)

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['date'] = datey_schema(app)  # type: ignore[index]
        return schema


@many_to_one['Note', Entity]('entity', 'notes')
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

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@type'] = 'https://schema.org/Thing'
        dump['text'] = self.text
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['text'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['required'].append(  # type: ignore[union-attr]
            'text',
        )
        return schema


@one_to_many[Entity, 'HasNotes']('notes', 'entity')
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


class Described(Describable, Dumpable[DictDump[Dump]]):
    description: str | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.description = None

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        if self.description is not None:
            dump['description'] = self.description
            dump.update({
                '@context': {},
            })
            dump['@context']['description'] = 'https://schema.org/description'  # type: ignore[index]
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['description'] = {  # type: ignore[index]
            'type': 'string'
        }
        return schema


class HasMediaType(Dumpable[DictDump[Dump]]):
    media_type: MediaType | None

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.media_type = None

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        if self.media_type is not None:
            dump['mediaType'] = self.media_type.dump(app)
        return dump


class Link(HasMediaType, Localized, Described, Describable, Dumpable[DictDump[Dump]]):
    url: str
    relationship: str | None
    label: str | None

    def __init__(self, url: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.url = url
        self.label = None
        self.relationship = None

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['url'] = self.url
        if self.label is not None:
            dump['label'] = self.label
        if self.relationship is not None:
            dump['relationship'] = self.relationship
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['label'] = {  # type: ignore[index]
            'type': 'string',
            'description': 'The human-readable label, or link text.',
        }
        schema['properties']['url'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
            'description': 'The full URL to the other resource.',
        }
        schema['properties']['relationship'] = {  # type: ignore[index]
            'type': 'string',
            'description': 'The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation).',
        }
        schema['properties']['locale'] = locale_schema(app)  # type: ignore[index]
        schema['properties']['mediaType'] = MediaType.schema(app)  # type: ignore[index]
        schema['required'].append(  # type: ignore[union-attr]
            'url',
        )
        schema['additionalProperties'] = False
        return schema


class HasLinks(Dumpable[DictDump[Dump]]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._links = set[Link]()

    @property
    def links(self) -> set[Link]:
        return self._links

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        if 'links' not in dump:
            dump['links'] = []
        for link in self.links:
            dump['links'].append(  # type: ignore[union-attr]
                link,
            )
        return dump


@many_to_many['Citation', 'HasCitations']('citations', 'facts')
class HasCitations(Dumpable[DictDump[Dump]]):
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

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        dump['citations'] = [
            app.static_url_generator.generate(citation)
            for citation
            in self.citations
            if is_identifiable(citation)
        ]
        return dump


@many_to_many[Entity, 'File']('entities', 'files')
class File(Described, HasPrivacy, HasMediaType, HasNotes, HasCitations, UserFacingEntity, Entity):
    def __init__(
        self,
        file_id: str | None,
        path: Path,
        media_type: MediaType | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(file_id, *args, **kwargs)
        self._path = path
        self.media_type = media_type

    @property
    def entities(self) -> EntityCollection[Any]:  # type: ignore[empty-body]
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
        return self.description if self.description else self._fallback_label

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['entities'] = [
            app.static_url_generator.generate(entity)
            for entity
            in self.entities
            if is_identifiable(entity)
        ]
        dump['notes'] = [
            app.static_url_generator.generate(note)
            for note
            in self.notes
            if is_identifiable(note)
        ]
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['mediaType'] = MediaType.schema(app)  # type: ignore[index]
        schema['properties']['notes'] = {  # type: ignore[index]
            'type': 'array',
            'items': Note.schema(app),
        }
        schema['properties']['entities'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
        }
        schema['required'].append(  # type: ignore[union-attr]
            'notes',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'entities',
        )
        return schema


@many_to_many[File, 'HasFiles']('files', 'entities')
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


@many_to_one['Source', 'Source']('contained_by', 'contains')
@one_to_many['Source', 'Source']('contains', 'contained_by')
@one_to_many['Citation', 'Source']('citations', 'source')
class Source(Dated, HasFiles, HasLinks, HasPrivacy, UserFacingEntity, Entity):
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
        return self.name if self.name else self._fallback_label

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@context'] = {
            'name': 'https://schema.org/name',
        }
        dump['@type'] = 'https://schema.org/Thing'
        dump['name'] = self.name
        dump['contains'] = [
            app.static_url_generator.generate(contained)
            for contained
            in self.contains
            if is_identifiable(contained)
        ]
        dump['citations'] = [
            app.static_url_generator.generate(citation)
            for citation
            in self.citations
            if is_identifiable(citation)
        ]
        if self.author is not None:
            dump['author'] = self.author
        if self.publisher is not None:
            dump['publisher'] = self.publisher
        if is_identifiable(self.contained_by):
            dump['containedBy'] = app.static_url_generator.generate(self.contained_by)
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['name'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['properties']['author'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['properties']['publisher'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['properties']['contains'] = {  # type: ignore[index]
            'type': 'array',
            'items': {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['containedBy'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
        }
        schema['required'].append(  # type: ignore[union-attr]
            'name',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'contains',
        )
        return schema


@many_to_many[HasCitations, 'Citation']('facts', 'citations')
@many_to_one[Source, 'Citation']('source', 'citations')
class Citation(Dated, HasFiles, HasPrivacy, UserFacingEntity, Entity):
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
        return self.location or self._fallback_label

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@type'] = 'https://schema.org/Thing'
        dump['facts'] = []
        if is_identifiable(self.source):
            dump['source'] = app.static_url_generator.generate(self.source)
        for fact in self.facts:
            if not is_identifiable(fact):
                continue
            dump['facts'].append(  # type: ignore[union-attr]
                app.static_url_generator.generate(fact),
            )
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['source'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri'
        }
        schema['properties']['facts'] = {  # type: ignore[index]
            'type': 'array',
            'items': {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['required'].append(  # type: ignore[union-attr]
            'facts',
        )
        return schema


class PlaceName(Localized, Dated, Describable, Dumpable[DictDump[Dump]]):
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

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        dump['name'] = self.name
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['name'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['required'].append(  # type: ignore[union-attr]
            'name',
        )
        return schema


@many_to_one_to_many['Place', 'Enclosure', 'Place']('enclosed_by', 'encloses', 'enclosed_by', 'encloses')
class Enclosure(Dated, HasCitations, Entity):
    encloses: Place | None
    enclosed_by: Place | None

    def __init__(
        self,
        encloses: Place | None,
        enclosed_by: Place | None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.encloses = encloses
        self.enclosed_by = enclosed_by


@one_to_many['Event', 'Place']('events', 'place')
@one_to_many['Place', 'Place']('enclosed_by', 'encloses')
@one_to_many['Place', 'Place']('encloses', 'enclosed_by')
class Place(HasLinks, UserFacingEntity, Entity):
    def __init__(
        self,
        place_id: str | None,
        names: list[PlaceName],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(place_id, *args, **kwargs)
        self._names = names
        self._coordinates = None

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
        return self._fallback_label

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@context'] = {
            'events': 'https://schema.org/event',
            'enclosedBy': 'https://schema.org/containedInPlace',
            'encloses': 'https://schema.org/containsPlace',
        }
        dump['@type'] = 'https://schema.org/Place',
        dump['names'] = self.names,
        dump['events'] = [
            app.static_url_generator.generate(event)
            for event
            in self.events
            if is_identifiable(event)
        ]
        dump['enclosedBy'] = [
            app.static_url_generator.generate(enclosure.enclosed_by)
            for enclosure
            in self.enclosed_by
            if is_identifiable(enclosure.enclosed_by)
        ]
        dump['encloses'] = [
            app.static_url_generator.generate(enclosure.encloses)
            for enclosure
            in self.encloses
            if is_identifiable(enclosure.encloses)
        ]
        if self.coordinates is not None:
            dump['coordinates'] = dump_coordinates(self.coordinates, app)
            dump['@context']['coordinates'] = 'https://schema.org/geo'  # type: ignore[index]
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['names'] = {  # type: ignore[index]
            "type": "array",
            "items": PlaceName.schema(app),
        }
        schema['properties']['coordinates'] = coordinates_schema(app)  # type: ignore[index]
        schema['properties']['encloses'] = {  # type: ignore[index]
            "type": "array",
            "items": {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['enclosedBy'] = {  # type: ignore[index]
            "type": "array",
            "items": {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['events'] = {  # type: ignore[index]
            "type": "array",
            "items": {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['required'].append(  # type: ignore[union-attr]
            'names',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'encloses',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'events',
        )
        return schema


class PresenceRole(Localizable, Describable, Dumpable[str]):
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @property
    def label(self) -> str:
        raise NotImplementedError(repr(self))

    def dump(self, app: App) -> str:
        return self.name()

    @classmethod
    def schema(cls, app: App) -> Schema:
        return {
            'type': 'string',
            'description': "'A person's role in an event.'",
        }


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


@many_to_one_to_many['Person', 'Presence', 'Event']('presences', 'person', 'event', 'presences')
class Presence(Entity):
    person: Person | None
    event: Event | None
    role: PresenceRole

    def __init__(
        self,
        person: Person | None,
        role: PresenceRole,
        event: Event | None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.person = person
        self.role = role
        self.event = event

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['role'] = self.role.dump(app)
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['role'] = PresenceRole.schema(app)  # type: ignore[index]
        schema['required'].append(  # type: ignore[union-attr]
            'role',
        )
        return schema


@many_to_one[Place, 'Event']('place', 'events')
@one_to_many[Presence, 'Event']('presences', 'event')
class Event(Dated, HasFiles, HasCitations, Described, HasPrivacy, UserFacingEntity, Entity):
    place: Place | None

    @property
    def label(self) -> str:
        label = self.type.label(self.localizer)
        if self.description is not None:
            label += f' ({self.description})'
        subjects = [
            presence.person
            for presence
            in self.presences
            if isinstance(presence.role, Subject) and presence.person is not None
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
        event_type: type[EventType],
        date: Datey | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(event_id, *args, **kwargs)
        self.date = date
        self._type = event_type

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
    def type(self) -> type[EventType]:
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

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@type'] = 'https://schema.org/Event'
        dump['type'] = self.type.name()

        dump['presences'] = [
            self._dump_presence(presence, app)
            for presence
            in self.presences
        ]
        if is_identifiable(self.place):
            dump['place'] = app.static_url_generator.generate(self.place)
            dump.update({
                '@context': {},
            })
            dump['@context']['place'] = 'https://schema.org/location'  # type: ignore[index]
        return dump

    def _dump_presence(self, presence: Presence, app: App) -> DictDump[Dump]:
        dump = presence.dump(app)
        dump['@context'] = {
            'person': 'https://schema.org/actor',
        }
        if is_identifiable(presence.person):
            dump['person'] = app.static_url_generator.generate(presence.person)
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['type'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['properties']['place'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
        }
        schema['properties']['presences'] = {  # type: ignore[index]
            'type': 'array',
            'items': cls._presence_schema(app),
        }
        schema['required'].append(  # type: ignore[union-attr]
            'type',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'presences',
        )
        schema['required'].append(  # type: ignore[union-attr]
            'citations',
        )
        return schema

    @classmethod
    def _presence_schema(cls, app: App) -> Schema:
        schema = Presence.schema(app)
        schema['properties']['person'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
        }
        schema['required'].append(  # type: ignore[union-attr]
            'person',
        )
        return schema


@total_ordering
@many_to_one['Person', 'PersonName']('person', 'names')
class PersonName(Localized, HasCitations, Entity):
    person: Person | None

    def __init__(
            self,
            person: Person | None,
            individual: str | None = None,
            affiliation: str | None = None,
            *args: Any,
            **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if not individual and not affiliation:
            raise ValueError('The individual and affiliation names must not both be empty.')
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return localizer._('Person name')

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return localizer._('Person names')

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
    def individual(self) -> str | None:
        return self._individual

    @property
    def affiliation(self) -> str | None:
        return self._affiliation

    @property
    def label(self) -> str:
        return self.localizer._('{individual_name} {affiliation_name}').format(
            individual_name='…' if not self.individual else self.individual,
            affiliation_name='…' if not self.affiliation else self.affiliation,
        )

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        if self.individual is not None or self.affiliation is not None:
            dump.update({
                '@context': {},
            })
        if self.individual is not None:
            dump['@context']['individual'] = 'https://schema.org/givenName'  # type: ignore[index]
            dump['individual'] = self.individual
        if self.affiliation is not None:
            dump['@context']['affiliation'] = 'https://schema.org/familyName'  # type: ignore[index]
            dump['affiliation'] = self.affiliation
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['individual'] = {  # type: ignore[index]
            'type': 'string',
        }
        schema['properties']['affiliation'] = {  # type: ignore[index]
            'type': 'string',
        }
        return schema


@total_ordering
@many_to_many['Person', 'Person']('parents', 'children')
@many_to_many['Person', 'Person']('children', 'parents')
@one_to_many[Presence, 'Person']('presences', 'person')
@one_to_many[PersonName, 'Person']('names', 'person')
class Person(HasFiles, HasCitations, HasLinks, HasPrivacy, UserFacingEntity, Entity):
    def __init__(self, person_id: str | None, *args: Any, **kwargs: Any):
        super().__init__(person_id, *args, **kwargs)

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
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id == other.id

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Person):
            return NotImplemented  # pragma: no cover
        return self.id > other.id

    @property
    def name(self) -> PersonName | None:
        try:
            return self.names[0]
        except IndexError:
            return None

    @property
    def alternative_names(self) -> list[PersonName]:
        return self.names.view[1:]

    @property
    def start(self) -> Event | None:
        with suppress(StopIteration):
            return next((
                presence.event
                for presence
                in self.presences
                if presence.event is not None and issubclass(presence.event.type, StartOfLifeEventType)
            ))
        return None

    @property
    def end(self) -> Event | None:
        with suppress(StopIteration):
            return next((
                presence.event
                for presence
                in self.presences
                if presence.event is not None and issubclass(presence.event.type, EndOfLifeEventType)
            ))
        return None

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
        return self.name.label if self.name else self._fallback_label

    def dump(self, app: App) -> DictDump[Dump]:
        dump = super().dump(app)
        dump['@context'] = {
            'parents': 'https://schema.org/parent',
            'children': 'https://schema.org/child',
            'siblings': 'https://schema.org/sibling',
        }
        dump['@type'] = 'https://schema.org/Person'
        dump['names'] = [
            name.dump(app)
            for name
            in self.names
        ],
        dump['parents'] = [
            app.static_url_generator.generate(parent)
            for parent
            in self.parents
            if is_identifiable(parent)
        ]
        dump['children'] = [
            app.static_url_generator.generate(child)
            for child
            in self.children
            if is_identifiable(child)
        ]
        dump['siblings'] = [
            app.static_url_generator.generate(sibling)
            for sibling
            in self.siblings
            if is_identifiable(sibling)
        ]
        dump['private'] = self.private
        dump['presences'] = [
            self._dump_presence(presence, app)
            for presence
            in self.presences
        ]
        return dump

    def _dump_presence(self, presence: Presence, app: App) -> DictDump[Dump]:
        dump = presence.dump(app)
        dump['@context'] = {
            'event': 'https://schema.org/Event',
        }
        if is_identifiable(presence.event):
            dump['event'] = None
        else:
            dump['event'] = app.static_url_generator.generate(presence.event)
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = object_schema(super().schema(app))
        schema['properties']['names'] = {  # type: ignore[index]
            'type': 'array',
            'items': PersonName.schema(app),
        }
        schema['properties']['parents'] = {  # type: ignore[index]
            'type': 'array',
            'items': {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['children'] = {  # type: ignore[index]
            'type': 'array',
            'items': {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['siblings'] = {  # type: ignore[index]
            'type': 'array',
            'items': {
                'type': 'string',
                'format': 'uri',
            },
        }
        schema['properties']['presences'] = {  # type: ignore[index]
            'type': 'array',
            'items': cls._presence_schema(app),
        }
        schema['required'].append('parents')  # type: ignore[union-attr]
        schema['required'].append('children')  # type: ignore[union-attr]
        schema['required'].append('siblings')  # type: ignore[union-attr]
        schema['required'].append('presences')  # type: ignore[union-attr]
        return schema

    @classmethod
    def _presence_schema(cls, app: App) -> Schema:
        schema = Presence.schema(app)
        schema['properties']['event'] = {  # type: ignore[index]
            'type': 'string',
            'format': 'uri',
        }
        schema['required'].append('event')  # type: ignore[union-attr]
        return schema


class Ancestry(Localizable):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._entities = MultipleTypesEntityCollection[Any](localizer=localizer)

    def __copy__(self) -> Ancestry:
        copied = self.__class__()
        copied.entities.append(*self.entities)
        return copied

    def __deepcopy__(self, memo: dict[Any, Any]) -> Ancestry:
        copied = self.__class__()
        copied.entities.append(*[copy.deepcopy(entity, memo) for entity in self.entities])
        return copied

    def __getstate__(self) -> FlattenedEntityCollection:
        entities = FlattenedEntityCollection()
        entities.add_entity(*self.entities)

        return entities

    def __setstate__(self, state: FlattenedEntityCollection) -> None:
        self._entities = MultipleTypesEntityCollection()
        self._entities.append(*state.unflatten())

    def _on_localizer_change(self) -> None:
        self._entities.localizer = self.localizer

    @property
    def entities(self) -> MultipleTypesEntityCollection[Any]:
        return self._entities
