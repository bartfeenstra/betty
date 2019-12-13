import json as stdjson
from tempfile import TemporaryDirectory, NamedTemporaryFile
from unittest import TestCase

from geopy import Point

from betty import json
from betty.ancestry import Place, Person, LocalizedName, Link, Event, Citation, Presence, Source, File, Note
from betty.config import Configuration
from betty.json import JSONEncoder
from betty.locale import Date


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
        place.encloses.add(Place('the_enclosed_place', []))
        place.links.add(
            Link('https://example.com/the-place', 'The Place Online'))
        place.events.add(Event('E1', Event.Type.BIRTH))
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
        sibling.parents.add(parent)

        person_id = 'the_person'
        person_family_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id, person_individual_name, person_family_name)
        person.parents.add(parent)
        person.children.add(child)
        person.private = False
        person.links.add(
            Link('https://example.com/the-person', 'The Person Online'))
        person.citations.add(
            Citation('the_citation', Source('the_source', 'The Source')))
        presence = Presence(Presence.Role.SUBJECT)
        presence.event = Event('the_event', Event.Type.BIRTH)
        person.presences.add(presence)

        expected = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'individualName': 'https://schema.org/givenName',
                'familyName': 'https://schema.org/familyName',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'familyName': person_family_name,
            'individualName': person_individual_name,
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
            Person('the_person').files.add(file)
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
        event = Event('the_event', Event.Type.BIRTH)
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
        event = Event('the_event', Event.Type.BIRTH)
        event.date = Date(2000, 1, 1)
        event.place = Place('the_place', [LocalizedName('The Place')])
        presence = Presence(Presence.Role.SUBJECT)
        presence.person = Person('the_person')
        event.presences.add(presence)
        event.citations.add(
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
                'year': 2000,
                'month': 1,
                'day': 1,
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
        source.date = Date(2000, 1, 1)
        source.contained_by = Source(
            'the_containing_source', 'The Containing Source')
        source.links.add(
            Link('https://example.com/the-person', 'The Person Online'))
        source.contains.add(
            Source('the_contained_source', 'The Contained Source'))
        source.citations.add(
            Citation('the_citation', Source('the_source', 'The Source')))
        expected = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'name': 'The Source',
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
            'claims': [],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_citation_should_encode_full(self):
        citation = Citation('the_citation', Source('the_source', 'The Source'))
        citation.description = 'The Source Description'
        citation.claims.add(Event('the_event', Event.Type.BIRTH))
        expected = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {
                'description': 'https://schema.org/description',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'source': '/source/the_source/index.json',
            'claims': [
                '/event/the_event/index.json'
            ],
            'description': 'The Source Description',
        }
        self.assert_encodes(expected, citation, 'citation')
