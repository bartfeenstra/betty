import json as stdjson
from os import path
from pathlib import Path
from typing import Dict, Any

import jsonschema
from geopy import Point
from jsonschema import RefResolver

from betty.asyncio import sync
from betty.model import Entity, get_entity_type_name, GeneratedEntityId
from betty.model.ancestry import Place, Person, PlaceName, Event, Described, HasLinks, HasCitations, Link, Dated, File, \
    Note, PersonName, HasMediaType, PresenceRole, EventType, Citation, Source
from betty.locale import Date, DateRange, Localized
from betty.media_type import MediaType
from betty.app import App
from betty.string import upper_camel_case_to_lower_camel_case


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
    def __init__(self, app: App, *args, **kwargs):
        stdjson.JSONEncoder.__init__(self, *args, **kwargs)
        self._app = app
        self._mappers = {
            Path: str,
            PlaceName: self._encode_localized_name,
            Place: self._encode_place,
            Point: self._encode_coordinates,
            Person: self._encode_person,
            PersonName: self._encode_person_name,
            File: self._encode_file,
            Event: self._encode_event,
            EventType: self._encode_event_type,
            PresenceRole: self._encode_presence_role,
            Date: self._encode_date,
            DateRange: self._encode_date_range,
            Citation: self._encode_citation,
            Source: self._encode_source,
            Link: self._encode_link,
            Note: self._encode_note,
            MediaType: self._encode_media_type,
        }

    @classmethod
    def get_factory(cls, app: App):
        return lambda *args, **kwargs: cls(app, *args, **kwargs)

    def default(self, o):
        for mapper_type in self._mappers:
            if isinstance(o, mapper_type):
                return self._mappers[mapper_type](o)
        stdjson.JSONEncoder.default(self, o)

    def _generate_url(self, resource: Any, media_type='application/json'):
        return self._app.url_generator.generate(resource, media_type)

    def _encode_schema(self, encoded: Dict, defintion: str) -> None:
        encoded['$schema'] = self._app.static_url_generator.generate(
            'schema.json#/definitions/%s' % defintion)

    @sync
    async def _encode_entity(self, encoded: Dict, entity: Entity) -> None:
        self._encode_schema(encoded, upper_camel_case_to_lower_camel_case(get_entity_type_name(entity.entity_type())))

        if 'links' not in encoded:
            encoded['links'] = []

        if not isinstance(entity.id, GeneratedEntityId):
            encoded['id'] = entity.id

            canonical = Link(self._generate_url(entity))
            canonical.relationship = 'canonical'
            canonical.media_type = 'application/json'
            encoded['links'].append(canonical)

            for locale_configuration in self._app.project.configuration.locales:
                if locale_configuration.locale == self._app.locale:
                    continue
                with self._app.activate_locale(locale_configuration.locale):
                    translation = Link(self._generate_url(entity))
                translation.relationship = 'alternate'
                translation.locale = locale_configuration.locale
                encoded['links'].append(translation)

            html = Link(self._generate_url(entity, media_type='text/html'))
            html.relationship = 'alternate'
            html.media_type = 'text/html'
            encoded['links'].append(html)

    def _encode_described(self, encoded: Dict, described: Described) -> None:
        if described.description is not None:
            encoded['description'] = described.description
            encoded.update({
                '@context': {},
            })
            encoded['@context']['description'] = 'https://schema.org/description'

    def _encode_dated(self, encoded: Dict, dated: Dated) -> None:
        if dated.date is not None:
            encoded['date'] = dated.date

    def _encode_date(self, date: Date) -> Dict:
        encoded = {}
        if date.year:
            encoded['year'] = date.year
        if date.month:
            encoded['month'] = date.month
        if date.day:
            encoded['day'] = date.day
        return encoded

    def _encode_date_range(self, date: DateRange) -> Dict:
        encoded = {}
        if date.start:
            encoded['start'] = date.start
        if date.end:
            encoded['end'] = date.end
        return encoded

    def _encode_localized(self, encoded: Dict, localized: Localized) -> None:
        if localized.locale is not None:
            encoded['locale'] = localized.locale

    def _encode_has_media_type(self, encoded: Dict, media: HasMediaType) -> None:
        if media.media_type is not None:
            encoded['mediaType'] = media.media_type

    def _encode_has_links(self, encoded: Dict, has_links: HasLinks) -> None:
        if 'links' not in encoded:
            encoded['links'] = []
        for link in has_links.links:
            encoded['links'].append(link)

    def _encode_link(self, link: Link) -> Dict:
        encoded = {
            'url': link.url,
        }
        if link.label is not None:
            encoded['label'] = link.label
        if link.relationship is not None:
            encoded['relationship'] = link.relationship
        self._encode_localized(encoded, link)
        self._encode_has_media_type(encoded, link)
        return encoded

    def _encode_has_citations(self, encoded: Dict, has_citations: HasCitations) -> None:
        encoded['citations'] = [self._generate_url(citation) for citation in has_citations.citations if not isinstance(citation.id, GeneratedEntityId)]

    def _encode_coordinates(self, coordinates: Point) -> Dict:
        return {
            '@context': {
                'latitude': 'https://schema.org/latitude',
                'longitude': 'https://schema.org/longitude',
            },
            '@type': 'https://schema.org/GeoCoordinates',
            'latitude': coordinates.latitude,
            'longitude': coordinates.longitude,
        }

    def _encode_localized_name(self, name: PlaceName) -> Dict:
        encoded = {
            'name': name.name,
        }
        self._encode_localized(encoded, name)
        return encoded

    def _encode_place(self, place: Place) -> Dict:
        encoded = {
            '@context': {
                'events': 'https://schema.org/event',
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
            },
            '@type': 'https://schema.org/Place',
            'names': place.names,
            'events': [self._generate_url(event) for event in place.events if not isinstance(event.id, GeneratedEntityId)],
            'enclosedBy': [self._generate_url(enclosure.enclosed_by) for enclosure in place.enclosed_by if not isinstance(enclosure.enclosed_by.id, GeneratedEntityId)],
            'encloses': [self._generate_url(enclosure.encloses) for enclosure in place.encloses if not isinstance(enclosure.encloses.id, GeneratedEntityId)],
        }
        self._encode_entity(encoded, place)
        self._encode_has_links(encoded, place)
        if place.coordinates is not None:
            encoded['coordinates'] = place.coordinates
            encoded['@context']['coordinates'] = 'https://schema.org/geo'
        return encoded

    def _encode_person(self, person: Person) -> Dict:
        encoded = {
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'names': list(person.names),
            'parents': [self._generate_url(parent) for parent in person.parents if not isinstance(parent.id, GeneratedEntityId)],
            'children': [self._generate_url(child) for child in person.children if not isinstance(child.id, GeneratedEntityId)],
            'siblings': [self._generate_url(sibling) for sibling in person.siblings if not isinstance(sibling.id, GeneratedEntityId)],
            'private': person.private,
            'presences': [],
        }
        for presence in person.presences:
            encoded['presences'].append({
                '@context': {
                    'event': 'https://schema.org/performerIn',
                },
                'role': presence.role,
                'event': None if isinstance(presence.event.id, GeneratedEntityId) else self._generate_url(presence.event),
            })
        self._encode_entity(encoded, person)
        self._encode_has_citations(encoded, person)
        self._encode_has_links(encoded, person)
        return encoded

    def _encode_person_name(self, name: PersonName) -> Dict:
        encoded = {}
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

    def _encode_file(self, file: File) -> Dict:
        encoded = {
            'entities': [self._generate_url(entity) for entity in file.entities if not isinstance(entity.id, GeneratedEntityId)],
            'notes': [self._generate_url(note) for note in file.notes if not isinstance(note.id, GeneratedEntityId)],
        }
        self._encode_entity(encoded, file)
        self._encode_has_media_type(encoded, file)
        return encoded

    def _encode_event(self, event: Event) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Event',
            'type': event.type,
            'presences': [{
                '@context': {
                    'person': 'https://schema.org/actor',
                },
                'role': presence.role,
                'person': None if isinstance(presence.person.id, GeneratedEntityId) else self._generate_url(presence.person),
            } for presence in event.presences],
        }
        self._encode_entity(encoded, event)
        self._encode_dated(encoded, event)
        self._encode_has_citations(encoded, event)
        if event.place is not None:
            encoded['place'] = None if isinstance(event.place.id, GeneratedEntityId) else self._generate_url(event.place)
            encoded.update({
                '@context': {},
            })
            encoded['@context']['place'] = 'https://schema.org/location'
        return encoded

    def _encode_event_type(self, event_type: EventType) -> str:
        return event_type.name()

    def _encode_presence_role(self, role: PresenceRole) -> str:
        return role.name()

    def _encode_citation(self, citation: Citation) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Thing',
            'facts': []
        }
        if not isinstance(citation.source.id, GeneratedEntityId):
            encoded['source'] = self._generate_url(citation.source)
        for fact in citation.facts:
            if isinstance(fact.id, GeneratedEntityId):
                continue
            encoded['facts'].append(self._generate_url(fact))
        self._encode_entity(encoded, citation)
        self._encode_dated(encoded, citation)
        return encoded

    def _encode_source(self, source: Source) -> Dict:
        encoded = {
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'name': source.name,
            'contains': [self._generate_url(contained) for contained in source.contains if not isinstance(contained.id, GeneratedEntityId)],
            'citations': [self._generate_url(citation) for citation in source.citations if not isinstance(citation.id, GeneratedEntityId)],
        }
        if source.author is not None:
            encoded['author'] = source.author
        if source.publisher is not None:
            encoded['publisher'] = source.publisher
        self._encode_entity(encoded, source)
        self._encode_dated(encoded, source)
        self._encode_has_links(encoded, source)
        if source.contained_by is not None and not isinstance(source.contained_by.id, GeneratedEntityId):
            encoded['containedBy'] = self._generate_url(source.contained_by)
        return encoded

    def _encode_note(self, note: Note) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Thing',
            'text': note.text,
        }
        self._encode_entity(encoded, note)
        return encoded

    def _encode_media_type(self, media_type: MediaType) -> str:
        return str(media_type)
