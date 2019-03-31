import json
from unittest import TestCase

from geopy import Point
from parameterized import parameterized

from betty.ancestry import Place, Ancestry
from betty.json import JSONEncoder


class JSONEncoderTest(TestCase):
    def assert_encodes(self, expected, data):
        self.assertAlmostEquals(expected, json.loads(
            json.dumps(data, cls=JSONEncoder)))

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
        place = Place(place_id, name)
        expected = {
            'id': place_id,
            'name': name,
        }
        self.assert_encodes(expected, place)

    def test_place_should_encode_full(self):
        place_id = 'the_place'
        name = 'The Place'
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        place = Place(place_id, name)
        place.coordinates = coordinates
        expected = {
            'id': place_id,
            'name': name,
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude,
            }
        }
        self.assert_encodes(expected, place)

    def test_ancestry_should_encode_minimal(self):
        ancestry = Ancestry()
        expected = {
            'places': {},
        }
        self.assert_encodes(expected, ancestry)

    def test_ancestry_should_encode_full(self):
        ancestry = Ancestry()
        place_id = 'the_place'
        name = 'The Place'
        place = Place(place_id, name)
        ancestry.places[place_id] = place
        expected = {
            'places': {
                place_id: {
                    'id': place_id,
                    'name': name,
                },
            },
        }
        self.assert_encodes(expected, ancestry)
