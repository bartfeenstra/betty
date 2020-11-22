import json as stdjson
from os import path
from typing import Dict, Any, Union

import jsonschema
from geopy import Point
from jsonschema import RefResolver

from betty.ancestry import Place, Person, PlaceName, Event, Described, HasLinks, HasCitations, Link, Dated, File, \
    Note, PersonName, IdentifiableEvent, Identifiable, IdentifiableSource, IdentifiableCitation, HasMediaType, Resource, \
    PresenceRole, EventType
from betty.locale import Date, DateRange, Localized
from betty.media_type import MediaType
from betty.plugin.deriver import DerivedEvent
from betty.site import Site


def validate(data: Any, schema_definition: str, site: Site) -> None:
    with open(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'schema.json')) as f:
        schema = stdjson.load(f)
    # @todo Can we set the schema ID somehow without making the entire JSON schema file a Jinja2 template?
    schema_id = site.static_url_generator.generate('schema.json', absolute=True)
    schema['$id'] = schema_id
    ref_resolver = RefResolver(schema_id, schema)
    jsonschema.validate(
        data, schema['definitions'][schema_definition], resolver=ref_resolver)


class JSONEncoder(stdjson.JSONEncoder):
    def __init__(self, site: Site, locale: str, *args, **kwargs):
        stdjson.JSONEncoder.__init__(self, *args, **kwargs)
        self._site = site
        self._locale = locale
        self._mappers = {
            PlaceName: self._encode_localized_name,
            Place: self._encode_place,
            Point: self._encode_coordinates,
            Person: self._encode_person,
            PersonName: self._encode_person_name,
            File: self._encode_file,
            DerivedEvent: self._encode_event,
            IdentifiableEvent: self._encode_identifiable_event,
            EventType: self._encode_event_type,
            PresenceRole: self._encode_presence_role,
            Date: self._encode_date,
            DateRange: self._encode_date_range,
            IdentifiableCitation: self._encode_identifiable_citation,
            IdentifiableSource: self._encode_identifiable_source,
            Link: self._encode_link,
            Note: self._encode_note,
            MediaType: self._encode_media_type,
        }

    @classmethod
    def get_factory(cls, site: Site, locale: str):
        return lambda *args, **kwargs: cls(site, locale, *args, **kwargs)

    def default(self, o):
        for mapper_type in self._mappers:
            if isinstance(o, mapper_type):
                return self._mappers[mapper_type](o)
        stdjson.JSONEncoder.default(self, o)

    def _generate_url(self, resource: Any, media_type='application/json', locale=None):
        locale = self._locale if locale is None else locale
        return self._site.localized_url_generator.generate(resource, media_type, locale=locale)

    def _encode_schema(self, encoded: Dict, defintion: str) -> None:
        encoded['$schema'] = self._site.static_url_generator.generate(
            'schema.json#/definitions/%s' % defintion)

    def _encode_identifiable_resource(self, encoded: Dict, resource: Union[Identifiable, Resource]) -> None:
        if 'links' not in encoded:
            encoded['links'] = []

        canonical = Link(self._generate_url(resource))
        canonical.relationship = 'canonical'
        canonical.media_type = 'application/json'
        encoded['links'].append(canonical)

        for locale in self._site.configuration.locales:
            if locale == self._locale:
                continue
            translation = Link(self._generate_url(resource, locale=locale))
            translation.relationship = 'alternate'
            translation.locale = locale
            encoded['links'].append(translation)

        html = Link(self._generate_url(resource, media_type='text/html'))
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
        encoded['citations'] = [self._generate_url(
            citation) for citation in has_citations.citations if isinstance(citation, Identifiable)]

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
            'id': place.id,
            'names': place.names,
            'events': [self._generate_url(event) for event in place.events],
            'enclosedBy': [self._generate_url(enclosure.enclosed_by) for enclosure in place.enclosed_by],
            'encloses': [self._generate_url(enclosure.encloses) for enclosure in place.encloses],
        }
        self._encode_schema(encoded, 'place')
        self._encode_identifiable_resource(encoded, place)
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
            'id': person.id,
            'names': list(person.names),
            'parents': [self._generate_url(parent) for parent in person.parents],
            'children': [self._generate_url(child) for child in person.children],
            'siblings': [self._generate_url(sibling) for sibling in person.siblings],
            'private': person.private,
            'presences': [],
        }
        for presence in person.presences:
            if isinstance(presence.event, Identifiable):
                encoded['presences'].append({
                    '@context': {
                        'event': 'https://schema.org/performerIn',
                    },
                    'role': presence.role,
                    'event': self._generate_url(presence.event),
                })
        self._encode_schema(encoded, 'person')
        self._encode_identifiable_resource(encoded, person)
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
            'id': file.id,
            'resources': [self._generate_url(entity) for entity in file.resources],
            'notes': file.notes,
        }
        self._encode_schema(encoded, 'file')
        self._encode_identifiable_resource(encoded, file)
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

    def _encode_identifiable_event(self, event: Event) -> Dict:
        encoded = self._encode_event(event)
        encoded['id'] = event.id
        self._encode_identifiable_resource(encoded, event)
        return encoded

    def _encode_event_type(self, event_type: EventType) -> str:
        return event_type.name()

    def _encode_presence_role(self, role: PresenceRole) -> str:
        return role.name()

    def _encode_identifiable_citation(self, citation: IdentifiableCitation) -> Dict:
        encoded = {
            '@type': 'https://schema.org/Thing',
            'id': citation.id,
            'facts': []
        }
        if isinstance(citation.source, Identifiable):
            encoded['source'] = self._generate_url(citation.source)
        for fact in citation.facts:
            if isinstance(fact, Identifiable):
                encoded['facts'].append(self._generate_url(fact))
        self._encode_schema(encoded, 'citation')
        self._encode_identifiable_resource(encoded, citation)
        self._encode_dated(encoded, citation)
        return encoded

    def _encode_identifiable_source(self, source: IdentifiableSource) -> Dict:
        encoded = {
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': source.id,
            'name': source.name,
            'contains': [self._generate_url(contained) for contained in source.contains if isinstance(contained, Identifiable)],
            'citations': [self._generate_url(citation) for citation in source.citations if isinstance(citation, Identifiable)],
        }
        if source.author is not None:
            encoded['author'] = source.author
        if source.publisher is not None:
            encoded['publisher'] = source.publisher
        self._encode_schema(encoded, 'source')
        self._encode_identifiable_resource(encoded, source)
        self._encode_dated(encoded, source)
        self._encode_has_links(encoded, source)
        if source.contained_by is not None:
            encoded['containedBy'] = self._generate_url(source.contained_by)
        return encoded

    def _encode_note(self, note: Note) -> Dict:
        return {
            'text': note.text,
        }

    def _encode_media_type(self, media_type: MediaType) -> str:
        return str(media_type)
