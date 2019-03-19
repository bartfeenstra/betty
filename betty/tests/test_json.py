import json
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Coordinates, Place, Ancestry
from betty.json import JSONEncoder


class JSONEncoderTest(TestCase):
    def assert_encodes(self, data, expected):
        self.assertEquals(json.loads(
            json.dumps(data, cls=JSONEncoder)), expected)

    @parameterized.expand([
        ('I am a string', 'I am a string'),
        (123, 123),
        ([], []),
        ((), []),
        ({}, {}),
    ])
    def test_builtin_type_should_encode(self, data, expected):
        self.assert_encodes(data, expected)

    def test_coordinates_should_encode(self):
        latitude = '12.345'
        longitude = '-54.321'
        coordinates = Coordinates(latitude, longitude)
        expected = {
            'latitude': latitude,
            'longitude': longitude,
        }
        self.assert_encodes(coordinates, expected)

    def test_place_should_encode_minimal(self):
        place_id = 'the_place'
        label = 'The Place'
        place = Place(place_id, label)
        expected = {
            'id': place_id,
            'label': label,
        }
        self.assert_encodes(place, expected)

    def test_place_should_encode_full(self):
        place_id = 'the_place'
        label = 'The Place'
        latitude = '12.345'
        longitude = '-54.321'
        coordinates = Coordinates(latitude, longitude)
        place = Place(place_id, label)
        place.coordinates = coordinates
        expected = {
            'id': place_id,
            'label': label,
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude,
            }
        }
        self.assert_encodes(place, expected)

    def test_ancestry_should_encode_minimal(self):
        ancestry = Ancestry()
        expected = {
            'places': {},
        }
        self.assert_encodes(ancestry, expected)

    def test_ancestry_should_encode_full(self):
        ancestry = Ancestry()
        place_id = 'the_place'
        label = 'The Place'
        place = Place(place_id, label)
        ancestry.places[place_id] = place
        expected = {
            'places': {
                place_id: {
                    'id': place_id,
                    'label': label,
                },
            },
        }
        self.assert_encodes(ancestry, expected)
