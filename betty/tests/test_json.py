import json
from tempfile import TemporaryDirectory
from unittest import TestCase

from geopy import Point
from parameterized import parameterized

from betty.ancestry import Place, Ancestry, Person, LocalizedName
from betty.config import Configuration
from betty.json import JSONEncoder
from betty.url import LocalizedUrlGenerator


class JSONEncoderTest(TestCase):
    def setUp(self) -> None:
        self._output_directory_path = TemporaryDirectory()
        configuration = Configuration(self._output_directory_path.name, 'https://example.com')
        self._url_generator = LocalizedUrlGenerator(configuration)

    def tearDown(self) -> None:
        self._output_directory_path.cleanup()

    def assert_encodes(self, expected, data):
        self.assertAlmostEquals(expected, json.loads(
            json.dumps(data, cls=JSONEncoder.get_factory(self._url_generator))))

    @parameterized.expand([
        ('I am a string', 'I am a string'),
        (123, 123),
        ([], []),
        ((), []),
        ({}, {}),
    ])
    def test_builtin_type_should_encode(self, data, expected):
        self.assert_encodes(expected, data)

    def test_coordinates_should_encode(self):
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        expected = {
            'latitude': latitude,
            'longitude': longitude,
        }
        self.assert_encodes(expected, coordinates)

    def test_place_should_encode_minimal(self):
        place_id = 'the_place'
        name = 'The Place'
        place = Place(place_id, [LocalizedName(name)])
        expected = {
            'id': place_id,
            'names': [
                {
                    'name': name,
                },
            ],
        }
        self.assert_encodes(expected, place)

    def test_place_should_encode_full(self):
        place_id = 'the_place'
        name = 'The Place'
        locale = 'nl-NL'
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        place = Place(place_id, [LocalizedName(name, locale)])
        place.coordinates = coordinates
        expected = {
            'id': place_id,
            'names': [
                {
                    'name': name,
                    'locale': 'nl-NL',
                },
            ],
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude,
            }
        }
        self.assert_encodes(expected, place)

    def test_person_should_encode_minimal(self):
        person_id = 'the_person'
        person = Person(person_id)
        expected = {
            '@context': {
                'individualName': 'https://schema.org/givenName',
                'familyName': 'https://schema.org/familyName',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
            },
            '@type': 'https://schema.org/Person',
            'id': person_id,
            'familyName': None,
            'individualName': None,
            'parents': [],
            'children': [],
            'private': None,
        }
        self.assert_encodes(expected, person)

    def test_person_should_encode_full(self):
        parent_id = 'the_parent'
        parent = Person(parent_id)

        child_id = 'the_child'
        child = Person(child_id)

        person_id = 'the_person'
        person_family_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id, person_individual_name, person_family_name)
        person.parents.add(parent)
        person.children.add(child)
        person.private = False

        expected = {
            'id': person_id,
            'family_name': person_family_name,
            'individual_name': person_individual_name,
            'parent_ids': [parent_id],
            'child_ids': [child_id],
            'private': False,
        }
        self.assert_encodes(expected, person)

    def test_ancestry_should_encode_minimal(self):
        ancestry = Ancestry()
        expected = {
            'places': {},
            'people': {},
        }
        self.assert_encodes(expected, ancestry)

    def test_ancestry_should_encode_full(self):
        ancestry = Ancestry()

        place_id = 'the_place'
        place_name = 'The Place'
        place_name_locale = 'nl-NL'
        place = Place(place_id, [LocalizedName(place_name, place_name_locale)])
        ancestry.places[place_id] = place

        person_id = 'the_person'
        person_family_name = 'Person'
        person_individual_name = 'The'
        person = Person(person_id, person_individual_name, person_family_name)
        ancestry.people[person_id] = person

        expected = {
            'places': {
                place_id: {
                    'id': place_id,
                    'names': [
                        {
                            'name': place_name,
                            'locale': 'nl-NL',
                        },
                    ],
                },
            },
            'people': {
                person_id: {
                    'id': person_id,
                    'family_name': person_family_name,
                    'individual_name': person_individual_name,
                    'parent_ids': [],
                    'child_ids': [],
                    'private': None,
                },
            },
        }
        self.assert_encodes(expected, ancestry)
