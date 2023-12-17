from __future__ import annotations

import json as stdjson
from os import path
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

import jsonschema
from geopy import Point
from jsonschema import RefResolver

from betty.app import App
from betty.asyncio import sync
from betty.locale import Date, DateRange, Localized, Localey, Str
from betty.media_type import MediaType
from betty.model import Entity, get_entity_type_name, GeneratedEntityId
from betty.model.ancestry import Place, Person, PlaceName, Event, Described, HasLinks, HasCitations, Link, Dated, File, \
    Note, PersonName, HasMediaType, PresenceRole, Citation, Source, is_public, Presence, HasPrivacy, is_private, \
    HasNotes
from betty.string import upper_camel_case_to_lower_camel_case

T = TypeVar('T')


def validate(data: Any, schema_definition: str, app: App) -> None:
    with open(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'schema.json'), encoding='utf-8') as f:
        json_data = f.read()
    schema = stdjson.loads(json_data)
    # @todo Can we set the schema ID somehow without making the entire JSON schema file a Jinja2 template?
    schema_id = app.static_url_generator.generate('schema.json', absolute=True)
    schema['$id'] = schema_id
    ref_resolver = RefResolver(schema_id, schema)
    jsonschema.validate(
        data, schema['definitions'][schema_definition], resolver=ref_resolver)


class JSONEncoder(stdjson.JSONEncoder):
    def __init__(
        self,
        app: App,
        *args: Any,
        **kwargs: Any,
    ):
        stdjson.JSONEncoder.__init__(self, *args, **kwargs)
        self._app = app
        self._mappers: dict[type[Any], Callable[[Any], Any]] = {
            Str: str,
            Path: str,
            PlaceName: self._encode_localized_name,
            Place: self._encode_place,
            Point: self._encode_coordinates,
            Person: self._encode_person,
            PersonName: self._encode_person_name,
            File: self._encode_file,
            Event: self._encode_event,
            PresenceRole: self._encode_presence_role,
            Date: self._encode_date,
            DateRange: self._encode_date_range,
            Citation: self._encode_citation,
            Source: self._encode_source,
            Link: self._encode_link,
            Note: self._encode_note,
            MediaType: self._encode_media_type,
        }

    def default(self, o: type[T]) -> Callable[[T], Any]:
        for mapper_type in self._mappers:
            if isinstance(o, mapper_type):
                return cast(Callable[[T], Any], self._mappers[mapper_type](o))
        return stdjson.JSONEncoder.default(self, o)  # type: ignore[no-any-return]

    def _generate_url(self, resource: Any, media_type='application/json', locale: Localey | None = None) -> str:
        return self._app.url_generator.generate(resource, media_type, locale=locale)

    def _encode_schema(self, encoded: dict[str, Any], defintion: str) -> None:
        encoded['$schema'] = self._app.static_url_generator.generate(
            'schema.json#/definitions/%s' % defintion)

    @sync
    async def _encode_entity(self, encoded: dict[str, Any], entity: Entity) -> None:
        self._encode_schema(encoded, upper_camel_case_to_lower_camel_case(get_entity_type_name(entity)))

        if 'links' not in encoded:
            encoded['links'] = []

        if '@context' not in encoded:
            encoded['@context'] = {}

        if not isinstance(entity.id, GeneratedEntityId):
            encoded['id'] = entity.id

            canonical = Link(
                self._generate_url(entity),
                relationship='canonical',
                media_type=MediaType('application/json'),
            )
            encoded['links'].append(canonical)

            if is_public(entity):
                for locale in self._app.project.configuration.locales:
                    localized_html_url = self._generate_url(entity, media_type='text/html', locale=locale)
                    localized_html_link = Link(
                        localized_html_url,
                        relationship='alternate',
                        media_type=MediaType('text/html'),
                        locale=locale,
                    )
                    encoded['links'].append(localized_html_link)

        if isinstance(entity, HasPrivacy):
            encoded['private'] = is_private(entity)
        if isinstance(entity, Dated):
            self._encode_dated(encoded, entity)
        if isinstance(entity, HasCitations):
            self._encode_has_citations(encoded, entity)
        if isinstance(entity, HasLinks):
            self._encode_has_links(encoded, entity)
        if isinstance(entity, HasNotes):
            self._encode_has_notes(encoded, entity)

    def _encode_described(self, encoded: dict[str, Any], described: Described) -> None:
        if described.description is not None:
            encoded['description'] = described.description
            encoded.update({
                '@context': {},
            })
            encoded['@context']['description'] = 'https://schema.org/description'

    def _encode_dated(self, encoded: dict[str, Any], dated: Dated) -> None:
        if is_public(dated):
            if dated.date is not None:
                encoded['date'] = dated.date

    def _encode_date(self, date: Date) -> dict[str, Any]:
        encoded: dict[str, Any] = {}
        if date.year:
            encoded['year'] = date.year
        if date.month:
            encoded['month'] = date.month
        if date.day:
            encoded['day'] = date.day
        return encoded

    def _encode_date_range(self, date: DateRange) -> dict[str, Any]:
        encoded: dict[str, Any] = {}
        if date.start:
            encoded['start'] = date.start
        if date.end:
            encoded['end'] = date.end
        return encoded

    def _encode_localized(self, encoded: dict[str, Any], localized: Localized) -> None:
        if localized.locale is not None:
            encoded['locale'] = localized.locale

    def _encode_has_media_type(self, encoded: dict[str, Any], media: HasMediaType) -> None:
        if is_public(media):
            if media.media_type is not None:
                encoded['mediaType'] = media.media_type

    def _encode_has_links(self, encoded: dict[str, Any], has_links: HasLinks) -> None:
        if 'links' not in encoded:
            encoded['links'] = []
        if is_public(has_links):
            for link in has_links.links:
                encoded['links'].append(link)

    def _encode_link(self, link: Link) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            'url': link.url,
        }
        if link.label is not None:
            encoded['label'] = link.label
        if link.relationship is not None:
            encoded['relationship'] = link.relationship
        self._encode_localized(encoded, link)
        self._encode_has_media_type(encoded, link)
        return encoded

    def _encode_has_citations(self, encoded: dict[str, Any], has_citations: HasCitations) -> None:
        encoded['citations'] = [
            self._generate_url(citation)
            for citation
            in has_citations.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]

    def _encode_coordinates(self, coordinates: Point) -> dict[str, Any]:
        return {
            '@context': {
                'latitude': 'https://schema.org/latitude',
                'longitude': 'https://schema.org/longitude',
            },
            '@type': 'https://schema.org/GeoCoordinates',
            'latitude': coordinates.latitude,
            'longitude': coordinates.longitude,
        }

    def _encode_localized_name(self, name: PlaceName) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            'name': name.name,
        }
        self._encode_localized(encoded, name)
        return encoded

    def _encode_place(self, place: Place) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@context': {
                'events': 'https://schema.org/event',
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
            },
            '@type': 'https://schema.org/Place',
            'names': place.names,
            'events': [
                self._generate_url(event)
                for event
                in place.events
                if not isinstance(event.id, GeneratedEntityId)
            ],
            'enclosedBy': [
                self._generate_url(enclosure.enclosed_by)
                for enclosure
                in place.enclosed_by
                if enclosure.enclosed_by is not None and not isinstance(enclosure.enclosed_by.id, GeneratedEntityId)
            ],
            'encloses': [
                self._generate_url(enclosure.encloses)
                for enclosure
                in place.encloses
                if enclosure.encloses is not None and not isinstance(enclosure.encloses.id, GeneratedEntityId)
            ],
        }
        self._encode_entity(encoded, place)
        if place.coordinates is not None:
            encoded['coordinates'] = place.coordinates
            encoded['@context']['coordinates'] = 'https://schema.org/geo'
        return encoded

    def _encode_person(self, person: Person) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'names': [],
            'parents': [
                self._generate_url(parent)
                for parent
                in person.parents
                if not isinstance(parent.id, GeneratedEntityId)
            ],
            'children': [
                self._generate_url(child)
                for child
                in person.children
                if not isinstance(child.id, GeneratedEntityId)
            ],
            'siblings': [
                self._generate_url(sibling)
                for sibling
                in person.siblings
                if not isinstance(sibling.id, GeneratedEntityId)
            ],
            'presences': [
                self._encode_person_presence(presence)
                for presence
                in person.presences
                if presence.event is not None and not isinstance(presence.event.id, GeneratedEntityId)
            ],
        }
        if person.public:
            for name in person.names:
                if name.public:
                    encoded['names'].append(name)
        self._encode_entity(encoded, person)
        return encoded

    def _encode_person_presence(self, presence: Presence) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@context': {
                'event': 'https://schema.org/performerIn',
            },
            'event': self._generate_url(presence.event),
        }
        if is_public(presence.person):
            encoded['role'] = presence.role
        return encoded

    def _encode_person_name(self, name: PersonName) -> dict[str, Any]:
        encoded: dict[str, Any] = {}
        if name.public:
            if name.individual is not None or name.affiliation is not None:
                encoded.update({
                    '@context': {},
                })
            if name.individual is not None:
                encoded['@context']['individual'] = 'https://schema.org/givenName'
                encoded['individual'] = name.individual
            if name.affiliation is not None:
                encoded['@context']['affiliation'] = 'https://schema.org/familyName'
                encoded['affiliation'] = name.affiliation
        return encoded

    def _encode_file(self, file: File) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            'entities': [
                self._generate_url(entity)
                for entity
                in file.entities
                if not isinstance(entity.id, GeneratedEntityId)
            ],
        }
        self._encode_entity(encoded, file)
        self._encode_has_media_type(encoded, file)
        return encoded

    def _encode_event(self, event: Event) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@type': 'https://schema.org/Event',
            'type': event.event_type.name(),
            'presences': [
                self._encode_event_presence(presence)
                for presence
                in event.presences
                if presence.person is not None and not isinstance(presence.person.id, GeneratedEntityId)
            ],
        }
        self._encode_entity(encoded, event)
        if event.place is not None and not isinstance(event.place.id, GeneratedEntityId):
            encoded['place'] = self._generate_url(event.place)
            encoded.update({
                '@context': {},
            })
            encoded['@context']['place'] = 'https://schema.org/location'
        return encoded

    def _encode_event_presence(self, presence: Presence) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@context': {
                'person': 'https://schema.org/actor',
            },
            'person': self._generate_url(presence.person),
        }
        if is_public(presence.person):
            encoded['role'] = presence.role
        return encoded

    def _encode_presence_role(self, role: PresenceRole) -> str:
        return role.name()

    def _encode_citation(self, citation: Citation) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@type': 'https://schema.org/Thing',
            'facts': []
        }
        if citation.source is not None and not isinstance(citation.source.id, GeneratedEntityId):
            encoded['source'] = self._generate_url(citation.source)
        for fact in citation.facts:
            if isinstance(fact.id, GeneratedEntityId):
                continue
            encoded['facts'].append(
                self._generate_url(fact),
            )
        self._encode_entity(encoded, citation)
        return encoded

    def _encode_source(self, source: Source) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@type': 'https://schema.org/Thing',
            'contains': [
                self._generate_url(contained)
                for contained
                in source.contains
                if not isinstance(contained.id, GeneratedEntityId)
            ],
            'citations': [
                self._generate_url(citation)
                for citation
                in source.citations
                if not isinstance(citation.id, GeneratedEntityId)
            ],
        }
        if source.contained_by is not None and not isinstance(source.contained_by.id, GeneratedEntityId):
            encoded['containedBy'] = self._generate_url(source.contained_by)
        self._encode_entity(encoded, source)
        if is_public(source):
            if source.name is not None:
                encoded['@context']['name'] = 'https://schema.org/name'
                encoded['name'] = source.name
            if source.author is not None:
                encoded['author'] = source.author
            if source.publisher is not None:
                encoded['publisher'] = source.publisher
        return encoded

    def _encode_has_notes(self, encoded: dict[str, Any], has_notes: HasNotes) -> None:
        encoded['notes'] = [
            self._generate_url(note)
            for note
            in has_notes.notes
            if not isinstance(note.id, GeneratedEntityId)
        ]

    def _encode_note(self, note: Note) -> dict[str, Any]:
        encoded: dict[str, Any] = {
            '@type': 'https://schema.org/Thing',
        }
        self._encode_entity(encoded, note)
        if is_public(note):
            encoded['text'] = note.text
        return encoded

    def _encode_media_type(self, media_type: MediaType) -> str:
        return str(media_type)
