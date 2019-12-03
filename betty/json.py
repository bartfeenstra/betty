import json as stdjson
from os import path
from typing import Dict, Any

import jsonschema
from geopy import Point
from jsonschema import RefResolver

from betty.ancestry import Place, Person, LocalizedName, Event, Citation, Source, Presence, Described, HasLinks, \
    HasCitations, Link, Dated, File, Note
from betty.config import Configuration
from betty.locale import Date
from betty.url import StaticPathUrlGenerator, SiteUrlGenerator


def validate(data: Any, schema_definition: str, configuration: Configuration) -> None:
    with open(path.join(path.dirname(__file__), 'resources', 'public', 'static', 'schema.json')) as f:
        schema = stdjson.load(f)
    # @todo Can we set the schema ID somehow without making the entire JSON schema file a Jinja2 template?
    schema_id = StaticPathUrlGenerator(configuration).generate('schema.json', absolute=True)
    schema['$id'] = schema_id
    ref_resolver = RefResolver(schema_id, schema)
    jsonschema.validate(data, schema['definitions'][schema_definition], resolver=ref_resolver)


class JSONEncoder(stdjson.JSONEncoder):
    def __init__(self, configuration: Configuration, locale: str, *args, **kwargs):
        stdjson.JSONEncoder.__init__(self, *args, **kwargs)
        self._url_generator = SiteUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._locale = locale
        self._mappers = {
            LocalizedName: self._encode_localized_name,
            Place: self._encode_place,
            Point: self._encode_coordinates,
            Person: self._encode_person,
            File: self._encode_file,
            Event: self._encode_event,
            Event.Type: self._encode_event_type,
            Presence.Role: self._encode_presence_role,
            Date: self._encode_date,
            Citation: self._encode_citation,
            Source: self._encode_source,
            Link: self._encode_link,
            Note: self._encode_note,
        }

    @classmethod
    def get_factory(cls, configuration: Configuration, locale: str):
        return lambda *args, **kwargs: cls(configuration, locale, *args, **kwargs)

    def default(self, o):
        otype = type(o)
        if otype in self._mappers:
            return self._mappers[otype](o)
        stdjson.JSONEncoder.default(self, o)

    def _generate_url(self, resource: Any):
        return self._url_generator.generate(resource, 'application/ld+json', locale=self._locale)

    def _encode_schema(self, encoded: Dict, defintion: str) -> None:
        encoded['$schema'] = self._static_url_generator.generate('schema.json#/definitions/%s' % defintion)

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

    def _encode_has_links(self, encoded: Dict, has_links: HasLinks) -> None:
        encoded['links'] = list(has_links.links)

    def _encode_link(self, link: Link) -> Dict:
        return {
            'url': link.url,
            'label': link.label,
        }

    def _encode_has_citations(self, encoded: Dict, has_citations: HasCitations) -> None:
        encoded['citations'] = [self._generate_url(citation) for citation in has_citations.citations]

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

    def _encode_localized_name(self, name: LocalizedName) -> Dict:
        encoded = {
            'name': name.name,
        }
        if name.locale:
            encoded['locale'] = name.locale
        return encoded

    def _encode_place(self, place: Place) -> Dict:
        encoded = {
            '@context': {
                'events': 'https://schema.org/event',
                'encloses': 'https://schema.org/containsPlace',
            },
            '@type': 'https://schema.org/Place',
            'id': place.id,
            'names': place.names,
            'events': [self._generate_url(event) for event in place.events],
            'encloses': [self._generate_url(enclosed) for enclosed in place.encloses]
        }
        self._encode_schema(encoded, 'place')
        self._encode_has_links(encoded, place)
        if place.coordinates is not None:
            encoded['coordinates'] = place.coordinates
            encoded['@context']['coordinates'] = 'https://schema.org/geo'
        if place.enclosed_by is not None:
            encoded['enclosedBy'] = self._generate_url(place.enclosed_by)
            encoded['@context']['enclosedBy'] = 'https://schema.org/containedInPlace'
        return encoded

    def _encode_person(self, person: Person) -> Dict:
        encoded = {
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person.id,
            'parents': [self._generate_url(parent) for parent in person.parents],
            'children': [self._generate_url(child) for child in person.children],
            'siblings': [self._generate_url(sibling) for sibling in person.siblings],
            'private': person.private,
            'presences': [{
                '@context': {
                    'event': 'https://schema.org/performerIn',
                },
                'role': presence.role,
                'event': self._generate_url(presence.event),
            } for presence in person.presences]
        }
        if person.individual_name is not None:
            encoded['@context']['individualName'] = 'https://schema.org/givenName'
            encoded['individualName'] = person.individual_name
        if person.family_name is not None:
            encoded['@context']['familyName'] = 'https://schema.org/familyName'
            encoded['familyName'] = person.family_name
        self._encode_schema(encoded, 'person')
        self._encode_has_citations(encoded, person)
        self._encode_has_links(encoded, person)
        return encoded

    def _encode_file(self, file: File) -> Dict:
        encoded = {
            'id': file.id,
            'entities': [self._generate_url(entity) for entity in file.entities],
            'notes': file.notes,
        }
        self._encode_schema(encoded, 'file')
        if file.type is not None:
            encoded['type'] = file.type
        return encoded

    def _encode_event(self, event: Event) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Event',
            'id': event.id,
            'type': event.type,
            'presences': [{
                '@context': {
                    'person': 'https://schema.org/actor',
                },
                'role': presence.role,
                'person': self._generate_url(presence.person),
            } for presence in event.presences],
        }
        self._encode_schema(encoded, 'event')
        self._encode_dated(encoded, event)
        self._encode_has_citations(encoded, event)
        if event.place is not None:
            encoded['place'] = self._generate_url(event.place)
            encoded.update({
                '@context': {},
            })
            encoded['@context']['place'] = 'https://schema.org/location'
        return encoded

    def _encode_event_type(self, event_type: Event.Type) -> str:
        return event_type.value

    def _encode_presence_role(self, role: Presence.Role) -> str:
        return role.value

    def _encode_citation(self, citation: Citation) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Thing',
            'id': citation.id,
            'source': self._generate_url(citation.source),
            'claims': [self._generate_url(claim) for claim in citation.claims]
        }
        self._encode_schema(encoded, 'citation')
        self._encode_described(encoded, citation)
        return encoded

    def _encode_source(self, source: Source) -> Dict:
        encoded = {
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': source.id,
            'name': source.name,
            'contains': [self._generate_url(contained) for contained in source.contains],
            'citations': [self._generate_url(citation) for citation in source.citations],
        }
        self._encode_schema(encoded, 'source')
        self._encode_dated(encoded, source)
        self._encode_has_links(encoded, source)
        if source.contained_by is not None:
            encoded['containedBy'] = self._generate_url(source.contained_by)
        return encoded

    def _encode_note(self, note: Note) -> Dict:
        return {
            'text': note.text,
        }
