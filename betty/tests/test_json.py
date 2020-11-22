import json as stdjson
from tempfile import TemporaryDirectory, NamedTemporaryFile

from geopy import Point

from betty import json
from betty.ancestry import Place, Person, PlaceName, Link, Presence, Source, File, Note, PersonName, \
    IdentifiableEvent, IdentifiableSource, IdentifiableCitation, Subject, Birth, Enclosure
from betty.config import Configuration, LocaleConfiguration
from betty.json import JSONEncoder
from betty.locale import Date, DateRange
from betty.media_type import MediaType
from betty.site import Site
from betty.tests import TestCase


class JSONEncoderTest(TestCase):
    def assert_encodes(self, expected, data, schema_definition: str):
        with TemporaryDirectory() as output_directory:
            configuration = Configuration(
                output_directory, '')
            configuration.locales.clear()
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            site = Site(configuration)
            encoded_data = stdjson.loads(stdjson.dumps(data, cls=JSONEncoder.get_factory(
                site, configuration.default_locale)))
            json.validate(encoded_data, schema_definition, site)
            self.assertEquals(expected, encoded_data)

    def test_coordinates_should_encode(self):
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        expected = {
            '@context': {
                'latitude': 'https://schema.org/latitude',
                'longitude': 'https://schema.org/longitude',
            },
            '@type': 'https://schema.org/GeoCoordinates',
            'latitude': latitude,
            'longitude': longitude,
        }
        self.assert_encodes(expected, coordinates, 'coordinates')

    def test_place_should_encode_minimal(self):
        place_id = 'the_place'
        name = 'The Place'
        place = Place(place_id, [PlaceName(name)])
        expected = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
                'events': 'https://schema.org/event'
            },
            '@type': 'https://schema.org/Place',
            'id': place_id,
            'names': [
                {
                    'name': name,
                },
            ],
            'enclosedBy': [],
            'encloses': [],
            'events': [],
            'links': [
                {
                    'url': '/en/place/the_place/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/place/the_place/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, place, 'place')

    def test_place_should_encode_full(self):
        place_id = 'the_place'
        name = 'The Place'
        locale = 'nl-NL'
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        place = Place(place_id, [PlaceName(name, locale)])
        place.coordinates = coordinates
        Enclosure(place, Place('the_enclosing_place', []))
        Enclosure(Place('the_enclosed_place', []), place)
        link = Link('https://example.com/the-place')
        link.label = 'The Place Online'
        place.links.add(link)
        place.events.append(IdentifiableEvent('E1', Birth()))
        expected = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
                'events': 'https://schema.org/event',
                'coordinates': 'https://schema.org/geo',
            },
            '@type': 'https://schema.org/Place',
            'id': place_id,
            'names': [
                {
                    'name': name,
                    'locale': 'nl-NL',
                },
            ],
            'events': [
                '/en/event/E1/index.json',
            ],
            'links': [
                {
                    'url': '/en/place/the_place/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/place/the_place/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
                {
                    'url': 'https://example.com/the-place',
                    'label': 'The Place Online',
                },
            ],
            'coordinates': {
                '@context': {
                    'latitude': 'https://schema.org/latitude',
                    'longitude': 'https://schema.org/longitude',
                },
                '@type': 'https://schema.org/GeoCoordinates',
                'latitude': latitude,
                'longitude': longitude,
            },
            'encloses': [
                '/en/place/the_enclosed_place/index.json',
            ],
            'enclosedBy': [
                '/en/place/the_enclosing_place/index.json',
            ],
        }
        self.assert_encodes(expected, place, 'place')

    def test_person_should_encode_minimal(self):
        person_id = 'the_person'
        person = Person(person_id)
        expected = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'names': [],
            'parents': [],
            'children': [],
            'siblings': [],
            'private': None,
            'presences': [],
            'citations': [],
            'links': [
                {
                    'url': '/en/person/the_person/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/person/the_person/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, person, 'person')

    def test_person_should_encode_full(self):
        parent_id = 'the_parent'
        parent = Person(parent_id)

        child_id = 'the_child'
        child = Person(child_id)

        sibling_id = 'the_sibling'
        sibling = Person(sibling_id)
        sibling.parents.append(parent)

        person_id = 'the_person'
        person_affiliation_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id)
        person.names.append(PersonName(person_individual_name, person_affiliation_name))
        person.parents.append(parent)
        person.children.append(child)
        person.private = False
        link = Link('https://example.com/the-person')
        link.label = 'The Person Online'
        person.links.add(link)
        person.citations.append(
            IdentifiableCitation('the_citation', Source('The Source')))
        Presence(person, Subject(), IdentifiableEvent('the_event', Birth()))

        expected = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'names': [
                {
                    '@context': {
                        'individual': 'https://schema.org/givenName',
                        'affiliation': 'https://schema.org/familyName',
                    },
                    'individual': person_individual_name,
                    'affiliation': person_affiliation_name,
                },
            ],
            'parents': [
                '/en/person/the_parent/index.json',
            ],
            'children': [
                '/en/person/the_child/index.json',
            ],
            'siblings': [
                '/en/person/the_sibling/index.json',
            ],
            'private': False,
            'presences': [
                {
                    '@context': {
                        'event': 'https://schema.org/performerIn',
                    },
                    'role': 'subject',
                    'event': '/en/event/the_event/index.json',
                },
            ],
            'citations': [
                '/en/citation/the_citation/index.json',
            ],
            'links': [
                {
                    'url': '/en/person/the_person/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/person/the_person/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
                {
                    'url': 'https://example.com/the-person',
                    'label': 'The Person Online',
                },
            ],
        }
        self.assert_encodes(expected, person, 'person')

    def test_file_should_encode_minimal(self):
        with NamedTemporaryFile() as f:
            file = File('the_file', f.name)
            expected = {
                '$schema': '/schema.json#/definitions/file',
                'id': 'the_file',
                'resources': [],
                'notes': [],
                'links': [
                    {
                        'url': '/en/file/the_file/index.json',
                        'relationship': 'canonical',
                        'mediaType': 'application/json',
                    },
                    {
                        'url': '/nl/file/the_file/index.json',
                        'relationship': 'alternate',
                        'locale': 'nl-NL',
                    },
                    {
                        'url': '/en/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_file_should_encode_full(self):
        with NamedTemporaryFile() as f:
            file = File('the_file', f.name)
            file.media_type = MediaType('text/plain')
            file.notes.append(Note('The Note'))
            Person('the_person').files.append(file)
            expected = {
                '$schema': '/schema.json#/definitions/file',
                'id': 'the_file',
                'mediaType': 'text/plain',
                'resources': [
                    '/en/person/the_person/index.json',
                ],
                'notes': [
                    {
                        'text': 'The Note',
                    },
                ],
                'links': [
                    {
                        'url': '/en/file/the_file/index.json',
                        'relationship': 'canonical',
                        'mediaType': 'application/json',
                    },
                    {
                        'url': '/nl/file/the_file/index.json',
                        'relationship': 'alternate',
                        'locale': 'nl-NL',
                    },
                    {
                        'url': '/en/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_event_should_encode_minimal(self):
        event = IdentifiableEvent('the_event', Birth())
        expected = {
            '$schema': '/schema.json#/definitions/event',
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'type': 'birth',
            'presences': [],
            'citations': [],
            'links': [
                {
                    'url': '/en/event/the_event/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/event/the_event/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, event, 'event')

    def test_event_should_encode_full(self):
        event = IdentifiableEvent('the_event', Birth())
        event.date = DateRange(Date(2000, 1, 1), Date(2019, 12, 31))
        event.place = Place('the_place', [PlaceName('The Place')])
        Presence(Person('the_person'), Subject(), event)
        event.citations.append(
            IdentifiableCitation('the_citation', Source('The Source')))
        expected = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
            },
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'type': 'birth',
            'presences': [
                {
                    '@context': {
                        'person': 'https://schema.org/actor',
                    },
                    'role': 'subject',
                    'person': '/en/person/the_person/index.json',
                },
            ],
            'citations': [
                '/en/citation/the_citation/index.json',
            ],
            'date': {
                'start': {
                    'year': 2000,
                    'month': 1,
                    'day': 1,
                },
                'end': {
                    'year': 2019,
                    'month': 12,
                    'day': 31,
                },
            },
            'place': '/en/place/the_place/index.json',
            'links': [
                {
                    'url': '/en/event/the_event/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/event/the_event/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, event, 'event')

    def test_source_should_encode_minimal(self):
        source = IdentifiableSource('the_source', 'The Source')
        expected = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'name': 'The Source',
            'contains': [],
            'citations': [],
            'links': [
                {
                    'url': '/en/source/the_source/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/source/the_source/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_source_should_encode_full(self):
        source = IdentifiableSource('the_source', 'The Source')
        source.author = 'The Author'
        source.publisher = 'The Publisher'
        source.date = Date(2000, 1, 1)
        source.contained_by = IdentifiableSource(
            'the_containing_source', 'The Containing Source')
        link = Link('https://example.com/the-source')
        link.label = 'The Source Online'
        source.links.add(link)
        source.contains.append(
            IdentifiableSource('the_contained_source', 'The Contained Source'))
        IdentifiableCitation('the_citation', source)
        expected = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'name': 'The Source',
            'author': 'The Author',
            'publisher': 'The Publisher',
            'contains': [
                '/en/source/the_contained_source/index.json',
            ],
            'citations': [
                '/en/citation/the_citation/index.json',
            ],
            'containedBy': '/en/source/the_containing_source/index.json',
            'date': {
                'year': 2000,
                'month': 1,
                'day': 1,
            },
            'links': [
                {
                    'url': '/en/source/the_source/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/source/the_source/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
                {
                    'url': 'https://example.com/the-source',
                    'label': 'The Source Online',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_citation_should_encode_minimal(self):
        citation = IdentifiableCitation('the_citation', Source('The Source'))
        expected = {
            '$schema': '/schema.json#/definitions/citation',
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'facts': [],
            'links': [
                {
                    'url': '/en/citation/the_citation/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/citation/the_citation/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_citation_should_encode_full(self):
        citation = IdentifiableCitation('the_citation', IdentifiableSource('the_source', 'The Source'))
        citation.description = 'The Source Description'
        citation.facts.append(IdentifiableEvent('the_event', Birth()))
        expected = {
            '$schema': '/schema.json#/definitions/citation',
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'source': '/en/source/the_source/index.json',
            'facts': [
                '/en/event/the_event/index.json'
            ],
            'links': [
                {
                    'url': '/en/citation/the_citation/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/nl/citation/the_citation/index.json',
                    'relationship': 'alternate',
                    'locale': 'nl-NL',
                },
                {
                    'url': '/en/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                },
            ],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_link_should_encode_minimal(self) -> None:
        link = Link('https://example.com')
        expected = {
            'url': 'https://example.com',
        }
        self.assert_encodes(expected, link, 'link')

    def test_link_should_encode_full(self) -> None:
        link = Link('https://example.com')
        link.label = 'The Link'
        link.relationship = 'external'
        link.locale = 'nl-NL'
        link.media_type = MediaType('text/html')
        expected = {
            'url': 'https://example.com',
            'relationship': 'external',
            'label': 'The Link',
            'locale': 'nl-NL',
            'mediaType': 'text/html',
        }
        self.assert_encodes(expected, link, 'link')
