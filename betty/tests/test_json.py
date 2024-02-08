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
    async def assert_encodes(self, data: Any, schema_definition: str) -> dict[str, Any]:
        app = App()
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration(
            'nl-NL',
            alias='nl',
        ))
        async with app:
            actual = stdjson.loads(stdjson.dumps(data, cls=app.json_encoder))
        json.validate(actual, schema_definition, app)
        return actual  # type: ignore[no-any-return]

    async def test_coordinates_should_encode(self) -> None:
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
        actual = await self.assert_encodes(coordinates, 'coordinates')
        assert expected == actual

    async def test_place_should_encode_minimal(self) -> None:
        place_id = 'the_place'
        name = 'The Place'
        place = Place(
            id=place_id,
            names=[PlaceName(name=name)],
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
                'names': 'https://schema.org/name',
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
                'events': 'https://schema.org/event'
            },
            '@id': '/place/the_place/index.json',
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
            'private': False,
        }
        actual = await self.assert_encodes(place, 'place')
        assert expected == actual

    async def test_place_should_encode_full(self) -> None:
        place_id = 'the_place'
        name = 'The Place'
        locale = 'nl-NL'
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        link = Link('https://example.com/the-place')
        link.label = 'The Place Online'
        place = Place(
            id=place_id,
            names=[PlaceName(
                name=name,
                locale=locale,
            )],
            events=[Event(
                id='E1',
                event_type=Birth,
            )],
            links=[link],
        )
        place.coordinates = coordinates
        Enclosure(encloses=place, enclosed_by=Place(id='the_enclosing_place'))
        Enclosure(encloses=Place(id='the_enclosed_place'), enclosed_by=place)
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/place',
            '@context': {
                'names': 'https://schema.org/name',
                'enclosedBy': 'https://schema.org/containedInPlace',
                'encloses': 'https://schema.org/containsPlace',
                'events': 'https://schema.org/event',
                'coordinates': 'https://schema.org/geo',
            },
            '@id': '/place/the_place/index.json',
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
            'private': False,
        }
        actual = await self.assert_encodes(place, 'place')
        assert expected == actual

    async def test_person_should_encode_minimal(self) -> None:
        person_id = 'the_person'
        person = Person(id=person_id)
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'names': 'https://schema.org/name',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@id': '/person/the_person/index.json',
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
        actual = await self.assert_encodes(person, 'person')
        assert expected == actual

    async def test_person_should_encode_full(self) -> None:
        parent_id = 'the_parent'
        parent = Person(id=parent_id)

        child_id = 'the_child'
        child = Person(id=child_id)

        sibling_id = 'the_sibling'
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = 'the_person'
        person_affiliation_name = 'Person'
        person_individual_name = 'The'
        person = Person(
            id=person_id,
            public=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link(
            'https://example.com/the-person',
            label='The Person Online',
        )
        person.links.append(link)
        person.citations.add(Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
        ))
        Presence(person, Subject(), Event(
            id='the_event',
            event_type=Birth,
        ))

        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'names': 'https://schema.org/name',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@id': '/person/the_person/index.json',
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
        actual = await self.assert_encodes(person, 'person')
        assert expected == actual

    async def test_person_should_encode_private(self) -> None:
        parent_id = 'the_parent'
        parent = Person(id=parent_id)

        child_id = 'the_child'
        child = Person(id=child_id)

        sibling_id = 'the_sibling'
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = 'the_person'
        person_affiliation_name = 'Person'
        person_individual_name = 'The'
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link('https://example.com/the-person')
        link.label = 'The Person Online'
        person.links.append(link)
        person.citations.add(Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
        ))
        Presence(person, Subject(), Event(
            id='the_event',
            event_type=Birth,
        ))

        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/person',
            '@context': {
                'names': 'https://schema.org/name',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
                'siblings': 'https://schema.org/sibling',
            },
            '@id': '/person/the_person/index.json',
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
        actual = await self.assert_encodes(person, 'person')
        assert expected == actual

    async def test_note_should_encode(self) -> None:
        note = Note(
            id='the_note',
            text='The Note',
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/note',
            '@context': {},
            '@id': '/note/the_note/index.json',
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
        actual = await self.assert_encodes(note, 'note')
        assert expected == actual

    async def test_note_should_encode_private(self) -> None:
        note = Note(
            id='the_note',
            text='The Note',
            private=True,
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/note',
            '@context': {},
            '@id': '/note/the_note/index.json',
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
        actual = await self.assert_encodes(note, 'note')
        assert expected == actual

    async def test_file_should_encode_minimal(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id='the_file',
                path=Path(f.name),
            )
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                '@id': '/file/the_file/index.json',
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
            actual = await self.assert_encodes(file, 'file')
            assert expected == actual

    async def test_file_should_encode_full(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id='the_file',
                path=Path(f.name),
                media_type=MediaType('text/plain'),
            )
            file.notes.add(Note(
                id='the_note',
                text='The Note',
            ))
            file.entities.add(Person(id='the_person'))
            file.citations.add(Citation(
                id='the_citation',
                source=Source(
                    id='the_source',
                    name='The Source',
                ),
            ))
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                '@id': '/file/the_file/index.json',
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
            actual = await self.assert_encodes(file, 'file')
            assert expected == actual

    async def test_file_should_encode_private(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id='the_file',
                path=Path(f.name),
                private=True,
                media_type=MediaType('text/plain'),
            )
            file.notes.add(Note(
                id='the_note',
                text='The Note',
            ))
            file.entities.add(Person(id='the_person'))
            file.citations.add(Citation(
                id='the_citation',
                source=Source(
                    id='the_source',
                    name='The Source',
                ),
            ))
            expected: dict[str, Any] = {
                '$schema': '/schema.json#/definitions/file',
                '@context': {},
                '@id': '/file/the_file/index.json',
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
            actual = await self.assert_encodes(file, 'file')
            assert expected == actual

    async def test_event_should_encode_minimal(self) -> None:
        event = Event(
            id='the_event',
            event_type=Birth,
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'presences': 'https://schema.org/performer',
            },
            '@id': '/event/the_event/index.json',
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': False,
            'type': 'birth',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'eventStatus': 'https://schema.org/EventScheduled',
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
        actual = await self.assert_encodes(event, 'event')
        assert expected == actual

    async def test_event_should_encode_full(self) -> None:
        event = Event(
            id='the_event',
            event_type=Birth,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id='the_place',
                names=[PlaceName(name='The Place')],
            ),
        )
        Presence(Person(id='the_person'), Subject(), event)
        event.citations.add(Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
        ))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
                'presences': 'https://schema.org/performer',
            },
            '@id': '/event/the_event/index.json',
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': False,
            'type': 'birth',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'eventStatus': 'https://schema.org/EventScheduled',
            'presences': [
                {
                    '@type': 'https://schema.org/Person',
                    'role': 'subject',
                    'person': '/person/the_person/index.json',
                },
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'date': {
                'start': {
                    '@context': {
                        'iso8601': ['https://schema.org/startDate'],
                    },
                    'year': 2000,
                    'month': 1,
                    'day': 1,
                    'iso8601': '2000-01-01',
                },
                'end': {
                    '@context': {
                        'iso8601': ['https://schema.org/endDate'],
                    },
                    'year': 2019,
                    'month': 12,
                    'day': 31,
                    'iso8601': '2019-12-31',
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
        actual = await self.assert_encodes(event, 'event')
        assert expected == actual

    async def test_event_should_encode_private(self) -> None:
        event = Event(
            id='the_event',
            event_type=Birth,
            private=True,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id='the_place',
                names=[PlaceName(name='The Place')],
            ),
        )
        Presence(Person(id='the_person'), Subject(), event)
        event.citations.add(Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
        ))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/event',
            '@context': {
                'place': 'https://schema.org/location',
                'presences': 'https://schema.org/performer',
            },
            '@id': '/event/the_event/index.json',
            '@type': 'https://schema.org/Event',
            'id': 'the_event',
            'private': True,
            'type': 'birth',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'eventStatus': 'https://schema.org/EventScheduled',
            'presences': [
                {
                    '@type': 'https://schema.org/Person',
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
        actual = await self.assert_encodes(event, 'event')
        assert expected == actual

    async def test_source_should_encode_minimal(self) -> None:
        source = Source(
            id='the_source',
            name='The Source',
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@id': '/source/the_source/index.json',
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
        actual = await self.assert_encodes(source, 'source')
        assert expected == actual

    async def test_source_should_encode_full(self) -> None:
        link = Link('https://example.com/the-source')
        link.label = 'The Source Online'
        source = Source(
            id='the_source',
            name='The Source',
            author='The Author',
            publisher='The Publisher',
            date=Date(2000, 1, 1),
            contained_by=Source(
                id='the_containing_source',
                name='The Containing Source',
            ),
            contains=[Source(
                id='the_contained_source',
                name='The Contained Source',
            )],
            links=[link],
        )
        Citation(
            id='the_citation',
            source=source,
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {
                'name': 'https://schema.org/name',
            },
            '@id': '/source/the_source/index.json',
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
                'iso8601': '2000-01-01',
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
        actual = await self.assert_encodes(source, 'source')
        assert expected == actual

    async def test_source_should_encode_private(self) -> None:
        link = Link('https://example.com/the-source')
        link.label = 'The Source Online'
        source = Source(
            id='the_source',
            name='The Source',
            author='The Author',
            publisher='The Publisher',
            date=Date(2000, 1, 1),
            contained_by=Source(
                id='the_containing_source',
                name='The Containing Source',
            ),
            contains=[Source(
                id='the_contained_source',
                name='The Contained Source',
            )],
            links=[link],
            private=True,
        )
        Citation(
            id='the_citation',
            source=source,
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {},
            '@id': '/source/the_source/index.json',
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
        }
        actual = await self.assert_encodes(source, 'source')
        actual.pop('links')
        assert expected == actual

    async def test_source_should_encode_with_private_associations(self) -> None:
        contained_by_source = Source(
            id='the_containing_source',
            name='The Containing Source',
        )
        contains_source = Source(
            id='the_contained_source',
            name='The Contained Source',
            private=True,
        )
        source = Source(
            id='the_source',
            contained_by=contained_by_source,
            contains=[contains_source],
        )
        Citation(
            id='the_citation',
            source=source,
            private=True,
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/source',
            '@context': {},
            '@id': '/source/the_source/index.json',
            '@type': 'https://schema.org/Thing',
            'id': 'the_source',
            'private': False,
            'contains': [
                '/source/the_contained_source/index.json',
            ],
            'citations': [
                '/citation/the_citation/index.json',
            ],
            'containedBy': '/source/the_containing_source/index.json',
        }
        actual = await self.assert_encodes(source, 'source')
        actual.pop('links')
        assert expected == actual

    async def test_citation_should_encode_minimal(self) -> None:
        citation = Citation(
            id='the_citation',
            source=Source(name='The Source'),
        )
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@id': '/citation/the_citation/index.json',
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
        actual = await self.assert_encodes(citation, 'citation')
        assert expected == actual

    async def test_citation_should_encode_full(self) -> None:
        citation = Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
        )
        citation.facts.add(Event(
            id='the_event',
            event_type=Birth,
        ))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@id': '/citation/the_citation/index.json',
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
        actual = await self.assert_encodes(citation, 'citation')
        assert expected == actual

    async def test_citation_should_encode_private(self) -> None:
        citation = Citation(
            id='the_citation',
            source=Source(
                id='the_source',
                name='The Source',
            ),
            private=True,
        )
        citation.facts.add(Event(
            id='the_event',
            event_type=Birth,
        ))
        expected: dict[str, Any] = {
            '$schema': '/schema.json#/definitions/citation',
            '@context': {},
            '@id': '/citation/the_citation/index.json',
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
        actual = await self.assert_encodes(citation, 'citation')
        assert expected == actual

    async def test_link_should_encode_minimal(self) -> None:
        link = Link('https://example.com')
        expected: dict[str, Any] = {
            'url': 'https://example.com',
        }
        actual = await self.assert_encodes(link, 'link')
        assert expected == actual

    async def test_link_should_encode_full(self) -> None:
        link = Link(
            'https://example.com',
            label='The Link',
            relationship='external',
            locale='nl-NL',
            media_type=MediaType('text/html'),
        )
        expected: dict[str, Any] = {
            'url': 'https://example.com',
            'relationship': 'external',
            'label': 'The Link',
            'locale': 'nl-NL',
            'mediaType': 'text/html',
        }
        actual = await self.assert_encodes(link, 'link')
        assert expected == actual
