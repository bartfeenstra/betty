import json as stdjson
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from geopy import Point

from betty import json
from betty.app import App
from betty.locale import Date, DateRange
from betty.media_type import MediaType
from betty.model.ancestry import Place, Person, PlaceName, Link, Presence, Source, File, Note, PersonName, \
    Subject, Enclosure, Citation, Event
from betty.model.event_type import Birth
from betty.project import LocaleConfiguration


class TestJSONEncoder:
    def assert_encodes(self, expected: Any, data: Any, schema_definition: str) -> None:
        app = App()
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        with app:
            encoded_data = stdjson.loads(stdjson.dumps(data, cls=app.json_encoder))
        json.validate(encoded_data, schema_definition, app)
        assert expected == encoded_data

    def test_coordinates_should_encode(self) -> None:
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        expected: dict[str, Any] = {
            '@context': {
                'latitude': 'https://schema.org/latitude',
                'longitude': 'https://schema.org/longitude',
            },
            '@type': 'https://schema.org/GeoCoordinates',
            'latitude': latitude,
            'longitude': longitude,
        }
        self.assert_encodes(expected, coordinates, 'coordinates')

    def test_place_should_encode_minimal(self) -> None:
        place_id = 'the_place'
        name = 'The Place'
        place = Place(place_id, [PlaceName(name)])
        expected: dict[str, Any] = {
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
                    'url': '/place/the_place/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, place, 'place')

    def test_place_should_encode_full(self) -> None:
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
        place.events.add(Event('E1', Birth))
        expected: dict[str, Any] = {
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
                '/event/E1/index.json',
            ],
            'links': [
                {
                    'url': '/place/the_place/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/place/the_place/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
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
                '/place/the_enclosed_place/index.json',
            ],
            'enclosedBy': [
                '/place/the_enclosing_place/index.json',
            ],
        }
        self.assert_encodes(expected, place, 'place')

    def test_person_should_encode_minimal(self) -> None:
        person_id = 'the_person'
        person = Person(person_id)
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'private': False,
            'names': [],
            'parents': [],
            'children': [],
            'siblings': [],
            'presences': [],
            'citations': [],
            'links': [
                {
                    'url': '/person/the_person/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, person, 'person')

    def test_person_should_encode_full(self) -> None:
        parent_id = 'the_parent'
        parent = Person(parent_id)

        child_id = 'the_child'
        child = Person(child_id)

        sibling_id = 'the_sibling'
        sibling = Person(sibling_id)
        sibling.parents.add(parent)

        person_id = 'the_person'
        person_affiliation_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id)
        PersonName(None, person, person_individual_name, person_affiliation_name)
        person.parents.add(parent)
        person.children.add(child)
        person.public = True
        link = Link('https://example.com/the-person')
        link.label = 'The Person Online'
        person.links.add(link)
        person.citations.add(Citation('the_citation', Source('The Source')))
        Presence(None, person, Subject(), Event('the_event', Birth))

        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'private': False,
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
            'presences': [
                {
                    '@context': {
                        'event': 'https://schema.org/performerIn',
                    },
                    'role': 'subject',
                    'event': '/event/the_event/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'links': [
                {
                    'url': '/person/the_person/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/person/the_person/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
                {
                    'url': 'https://example.com/the-person',
                    'label': 'The Person Online',
                },
            ],
        }
        self.assert_encodes(expected, person, 'person')

    def test_person_should_encode_private(self) -> None:
        parent_id = 'the_parent'
        parent = Person(parent_id)

        child_id = 'the_child'
        child = Person(child_id)

        sibling_id = 'the_sibling'
        sibling = Person(sibling_id)
        sibling.parents.add(parent)

        person_id = 'the_person'
        person_affiliation_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id)
        PersonName(None, person, person_individual_name, person_affiliation_name)
        person.parents.add(parent)
        person.children.add(child)
        person.private = True
        link = Link('https://example.com/the-person')
        link.label = 'The Person Online'
        person.links.add(link)
        person.citations.add(Citation('the_citation', Source('The Source')))
        Presence(None, person, Subject(), Event('the_event', Birth))

        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'names': [],
            'parents': [
                '/person/the_parent/index.json',
            ],
            'children': [
                '/person/the_child/index.json',
            ],
            'siblings': [
                '/person/the_sibling/index.json',
            ],
            'private': True,
            'presences': [
                {
                    '@context': {
                        'event': 'https://schema.org/performerIn',
                    },
                    'event': '/event/the_event/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'links': [
                {
                    'url': '/person/the_person/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
            ],
        }
        self.assert_encodes(expected, person, 'person')

    def test_note_should_encode(self) -> None:
        note = Note('the_note', 'The Note')
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/note',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_note',
            'private': False,
            'text': 'The Note',
            'links': [
                {
                    'url': '/note/the_note/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/note/the_note/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/note/the_note/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, note, 'note')

    def test_note_should_encode_private(self) -> None:
        note = Note('the_note', 'The Note')
        note.private = True
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/note',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_note',
            'private': True,
            'links': [
                {
                    'url': '/note/the_note/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
            ],
        }
        self.assert_encodes(expected, note, 'note')

    def test_file_should_encode_minimal(self) -> None:
        with NamedTemporaryFile() as f:
            file = File('the_file', Path(f.name))
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                'id': 'the_file',
                'private': False,
                'entities': [],
                'citations': [],
                'notes': [],
                'links': [
                    {
                        'url': '/file/the_file/index.json',
                        'relationship': 'canonical',
                        'mediaType': 'application/json',
                    },
                    {
                        'url': '/en/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                        'locale': 'en-US',
                    },
                    {
                        'url': '/nl/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                        'locale': 'nl-NL',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_file_should_encode_full(self) -> None:
        with NamedTemporaryFile() as f:
            file = File('the_file', Path(f.name))
            file.media_type = MediaType('text/plain')
            file.notes.add(Note('the_note', 'The Note'))
            file.entities.add(Person('the_person'))
            file.citations.add(Citation('the_citation', Source('The Source')))
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                'id': 'the_file',
                'private': False,
                'mediaType': 'text/plain',
                'entities': [
                    '/person/the_person/index.json',
                ],
                'citations': [
                    '/citation/the_citation/index.json',
                ],
                'notes': [
                    '/note/the_note/index.json',
                ],
                'links': [
                    {
                        'url': '/file/the_file/index.json',
                        'relationship': 'canonical',
                        'mediaType': 'application/json',
                    },
                    {
                        'url': '/en/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                        'locale': 'en-US',
                    },
                    {
                        'url': '/nl/file/the_file/index.html',
                        'relationship': 'alternate',
                        'mediaType': 'text/html',
                        'locale': 'nl-NL',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_file_should_encode_private(self) -> None:
        with NamedTemporaryFile() as f:
            file = File('the_file', Path(f.name))
            file.media_type = MediaType('text/plain')
            file.notes.add(Note('the_note', 'The Note'))
            file.entities.add(Person('the_person'))
            file.citations.add(Citation('the_citation', Source('The Source')))
            file.private = True
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                'id': 'the_file',
                'private': True,
                'entities': [
                    '/person/the_person/index.json',
                ],
                'citations': [
                    '/citation/the_citation/index.json',
                ],
                'notes': [
                    '/note/the_note/index.json',
                ],
                'links': [
                    {
                        'url': '/file/the_file/index.json',
                        'relationship': 'canonical',
                        'mediaType': 'application/json',
                    },
                ],
            }
            self.assert_encodes(expected, file, 'file')

    def test_event_should_encode_minimal(self) -> None:
        event = Event('the_event', Birth)
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {},
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': False,
            'type': 'birth',
            'presences': [],
            'citations': [],
            'links': [
                {
                    'url': '/event/the_event/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, event, 'event')

    def test_event_should_encode_full(self) -> None:
        event = Event('the_event', Birth)
        event.date = DateRange(Date(2000, 1, 1), Date(2019, 12, 31))
        event.place = Place('the_place', [PlaceName('The Place')])
        Presence(None, Person('the_person'), Subject(), event)
        event.citations.add(Citation('the_citation', Source('The Source')))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
            },
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': False,
            'type': 'birth',
            'presences': [
                {
                    '@context': {
                        'person': 'https://schema.org/actor',
                    },
                    'role': 'subject',
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
            'links': [
                {
                    'url': '/event/the_event/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/event/the_event/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, event, 'event')

    def test_event_should_encode_private(self) -> None:
        event = Event('the_event', Birth)
        event.date = DateRange(Date(2000, 1, 1), Date(2019, 12, 31))
        event.place = Place('the_place', [PlaceName('The Place')])
        Presence(None, Person('the_person'), Subject(), event)
        event.citations.add(Citation('the_citation', Source('The Source')))
        event.private = True
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
            },
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': True,
            'type': 'birth',
            'presences': [
                {
                    '@context': {
                        'person': 'https://schema.org/actor',
                    },
                    'role': 'subject',
                    'person': '/person/the_person/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'place': '/place/the_place/index.json',
            'links': [
                {
                    'url': '/event/the_event/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
            ],
        }
        self.assert_encodes(expected, event, 'event')

    def test_source_should_encode_minimal(self) -> None:
        source = Source('the_source', 'The Source')
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'private': False,
            'name': 'The Source',
            'contains': [],
            'citations': [],
            'links': [
                {
                    'url': '/source/the_source/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_source_should_encode_full(self) -> None:
        source = Source('the_source', 'The Source')
        source.author = 'The Author'
        source.publisher = 'The Publisher'
        source.date = Date(2000, 1, 1)
        source.contained_by = Source('the_containing_source', 'The Containing Source')
        link = Link('https://example.com/the-source')
        link.label = 'The Source Online'
        source.links.add(link)
        source.contains.add(Source('the_contained_source', 'The Contained Source'))
        Citation('the_citation', source)
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'private': False,
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
                    'url': '/source/the_source/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/source/the_source/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
                {
                    'url': 'https://example.com/the-source',
                    'label': 'The Source Online',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_source_should_encode_private(self) -> None:
        source = Source('the_source', 'The Source')
        source.author = 'The Author'
        source.publisher = 'The Publisher'
        source.date = Date(2000, 1, 1)
        source.contained_by = Source('the_containing_source', 'The Containing Source')
        link = Link('https://example.com/the-source')
        link.label = 'The Source Online'
        source.links.add(link)
        source.contains.add(Source('the_contained_source', 'The Contained Source'))
        Citation('the_citation', source)
        source.private = True
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'private': True,
            'contains': [
                '/source/the_contained_source/index.json',
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'containedBy': '/source/the_containing_source/index.json',
            'links': [
                {
                    'url': '/source/the_source/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
            ],
        }
        self.assert_encodes(expected, source, 'source')

    def test_citation_should_encode_minimal(self) -> None:
        citation = Citation('the_citation', Source(None, 'The Source'))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'private': False,
            'facts': [],
            'links': [
                {
                    'url': '/citation/the_citation/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_citation_should_encode_full(self) -> None:
        citation = Citation('the_citation', Source('the_source', 'The Source'))
        citation.facts.add(Event('the_event', Birth))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'private': False,
            'source': '/source/the_source/index.json',
            'facts': [
                '/event/the_event/index.json'
            ],
            'links': [
                {
                    'url': '/citation/the_citation/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
                {
                    'url': '/en/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'en-US',
                },
                {
                    'url': '/nl/citation/the_citation/index.html',
                    'relationship': 'alternate',
                    'mediaType': 'text/html',
                    'locale': 'nl-NL',
                },
            ],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_citation_should_encode_private(self) -> None:
        citation = Citation('the_citation', Source('the_source', 'The Source'))
        citation.facts.add(Event('the_event', Birth))
        citation.private = True
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@type': 'https://schema.org/Thing',
            'id': 'the_citation',
            'private': True,
            'source': '/source/the_source/index.json',
            'facts': [
                '/event/the_event/index.json'
            ],
            'links': [
                {
                    'url': '/citation/the_citation/index.json',
                    'relationship': 'canonical',
                    'mediaType': 'application/json',
                },
            ],
        }
        self.assert_encodes(expected, citation, 'citation')

    def test_link_should_encode_minimal(self) -> None:
        link = Link('https://example.com')
        expected: dict[str, Any] = {
            'url': 'https://example.com',
        }
        self.assert_encodes(expected, link, 'link')

    def test_link_should_encode_full(self) -> None:
        link = Link('https://example.com')
        link.label = 'The Link'
        link.relationship = 'external'
        link.locale = 'nl-NL'
        link.media_type = MediaType('text/html')
        expected: dict[str, Any] = {
            'url': 'https://example.com',
            'relationship': 'external',
            'label': 'The Link',
            'locale': 'nl-NL',
            'mediaType': 'text/html',
        }
        self.assert_encodes(expected, link, 'link')
