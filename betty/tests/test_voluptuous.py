from unittest import TestCase

from voluptuous import Invalid

from betty.voluptuous import MapDict


class MapDictTest(TestCase):
    def test_with_empty_dict(self):
        data = {}
        sut = MapDict(str, str)
        self.assertDictEqual(data, sut(data))

    def test_with_valid_dict(self):
        data = {
            'SomeKey': 'SomeValue',
        }
        sut = MapDict(str, str)
        self.assertDictEqual(data, sut(data))

    def test_with_invalid_key(self):
        data = {
            9: 'SomeValue',
        }
        sut = MapDict(str, str)
        with self.assertRaises(Invalid):
            sut(data)

    def test_with_invalid_value(self):
        data = {
            'SomeKey': 9,
        }
        sut = MapDict(str, str)
        with self.assertRaises(Invalid):
            sut(data)
