import json as stdjson
from tempfile import TemporaryDirectory, NamedTemporaryFile
from unittest import TestCase

from geopy import Point

from betty import json
from betty.ancestry import Place, Person, LocalizedName, Link, Event, Citation, Presence, Source, File, Note, \
    PersonName, IdentifiableEvent
from betty.config import Configuration
from betty.json import JSONEncoder
from betty.locale import Date, DateRange


class JSONEncoderTest(TestCase):
    maxDiff = None

    def assert_encodes(self, expected, data, schema_definition: str):
        with TemporaryDirectory() as output_directory:
            configuration = Configuration(
                output_directory, '')
            encoded_data = stdjson.loads(stdjson.dumps(data, cls=JSONEncoder.get_factory(
                configuration, configuration.default_locale)))
            json.validate(encoded_data, schema_definition, configuration)
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
        place = Place(place_id, [LocalizedName(name)])
        expected = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
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
            'encloses': [],
            'events': [],
            'links': [],
        }
        self.assert_encodes(expected, place, 'place')

    def test_place_should_encode_full(self):
        place_id = 'the_place'
        name = 'The Place'
        locale = 'nl-NL'
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        place = Place(place_id, [LocalizedName(name, locale)])
        place.coordinates = coordinates
        place.enclosed_by = Place('the_enclosing_place', [])
        place.encloses.append(Place('the_enclosed_place', []))
        place.links.add(
            Link('https://example.com/the-place', 'The Place Online'))
        place.events.append(IdentifiableEvent('E1', Event.Type.BIRTH))
        expected = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
                'encloses': 'https://schema.org/containsPlace',
                'events': 'https://schema.org/event',
                'enclosedBy': 'https://schema.org/containedInPlace',
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
                '/event/E1/index.json',
            ],
            'links': [
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
                '/place/the_enclosed_place/index.json',
            ],
            'enclosedBy': '/place/the_enclosing_place/index.json',
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
            'links': [],
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
        person.links.add(
            Link('https://example.com/the-person', 'The Person Online'))
        person.citations.append(
            Citation('the_citation', Source('the_source', 'The Source')))
        Presence(person, Presence.Role.SUBJECT, IdentifiableEvent('the_event', Event.Type.BIRTH))

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
                '/person/the_parent/index.json',
            ],
            'children': [
                '/person/the_child/index.json',
            ],
            'siblings': [
                '/person/the_sibling/index.json',
            ],
            'private': False,
            'presences': [
                {
                    '@context': {
                        'event': 'https://schema.org/performerIn',
                    },
                    'role': Presence.Role.SUBJECT.value,
                    'event': '/event/the_event/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'links': [
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
                'entities': [],
                'notes': [],
            }
            self.assert_encodes(expected, file, 'file')

    def test_file_should_encode_full(self):
        with NamedTemporaryFile() as f:
            file = File('the_file', f.name)
            file.type = 'text/plain'
            file.notes.append(Note('The Note'))
            Person('the_person').files.append(file)
            expected = {
                '$schema': '/schema.json#/definitions/file',
                'id': 'the_file',
                'type': 'text/plain',
                'entities': [
                    '/person/the_person/index.json',
                ],
                'notes': [
                    {
                        'text': 'The Note',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_event_should_encode_minimal(self):
        event = IdentifiableEvent('the_event', Event.Type.BIRTH)
        expected = {
            '$schema': '/schema.json#/definitions/event',
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'type': Event.Type.BIRTH.value,
            'presences': [],
            'citations': [],
        }
        self.assert_encodes(expected, event, 'event')

    def test_event_should_encode_full(self):
        event = IdentifiableEvent('the_event', Event.Type.BIRTH)
        event.date = DateRange(Date(2000, 1, 1), Date(2019, 12, 31))
        event.place = Place('the_place', [LocalizedName('The Place')])
        Presence(Person('the_person'), Presence.Role.SUBJECT, event)
        event.citations.append(
            Citation('the_citation', Source('the_source', 'The Source')))
        expected = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
            },
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'type': Event.Type.BIRTH.value,
            'presences': [
                {
                    '@context': {
                        'person': 'https://schema.org/actor',
                    },
                    'role': Presence.Role.SUBJECT.value,
                    'person': '/person/the_person/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
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
            'place': '/place/the_place/index.json',
        }
        self.assert_encodes(expected, event, 'event')

    def test_source_should_encode_minimal(self):
        source = Source('the_source', 'The Source')
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
            'links': [],
        }
        self.assert_encodes(expected, source, 'source')

    def test_source_should_encode_full(self):
        source = Source('the_source', 'The Source')
        source.author = 'The Author'
        source.publisher = 'The Publisher'
        source.date = Date(2000, 1, 1)
        source.contained_by = Source(
            'the_containing_source', 'The Containing Source')
        source.links.add(
            Link('https://example.com/the-person', 'The Person Online'))
        source.contains.append(
            Source('the_contained_source', 'The Contained Source'))
        source.citations.append(
            Citation('the_citation', Source('the_source', 'The Source')))
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
                '/source/the_contained_source/index.json',
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'containedBy': '/source/the_containing_source/index.json',
            'date': {
                'year': 2000,
                'month': 1,
                'day': 1,
            },
            'links': [
                {
                    'url': 'https://example.com/the-person',
                    'label': 'The Person Online',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_citation_should_encode_minimal(self):
        citation = Citation('the_citation', Source('the_source', 'The Source'))
        expected = {
            '$schema': '/schema.json#/definitions/citation',
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'source': '/source/the_source/index.json',
            'facts': [],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_citation_should_encode_full(self):
        citation = Citation('the_citation', Source('the_source', 'The Source'))
        citation.description = 'The Source Description'
        citation.facts.append(IdentifiableEvent('the_event', Event.Type.BIRTH))
        expected = {
            '$schema': '/schema.json#/definitions/citation',
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'source': '/source/the_source/index.json',
            'facts': [
                '/event/the_event/index.json'
            ],
        }
        self.assert_encodes(expected, citation, 'citation')
