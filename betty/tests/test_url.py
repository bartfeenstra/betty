from typing import Any
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Person, Event, Place, File, Source, Citation
from betty.config import Configuration
from betty.url import UrlGenerator


class UrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example/', 'example/'),
        ('/example/', '/example/'),
    ])
    def test_generate_for_string_target(self, expected: str, target: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(target))

    @parameterized.expand([
        ('https://example.com/example', 'example'),
        ('https://example.com/example', '/example'),
        ('https://example.com/example/', 'example/'),
        ('https://example.com/example/', '/example/'),
    ])
    def test_generate_for_string_target_absolute(self, expected: str, target: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(target, True))

    @parameterized.expand([
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Event.Type.DEATH)),
        ('/place/P1/index.html', Place('P1', 'Place 1')),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1')),
    ])
    def test_generate_for_identifiable_target(self, expected: str, target: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(target))

    @parameterized.expand([
        ('/person/P1/', Person('P1')),
        ('/event/E1/', Event('E1', Event.Type.DEATH)),
        ('/place/P1/', Place('P1', 'Place 1')),
        ('/file/F1/', File('F1', '/tmp')),
        ('/source/S1/', Source('S1', 'Source 1')),
        ('/citation/C1/', Citation('C1')),
    ])
    def test_generate_for_identifiable_target_with_clean_urls(self, expected: str, target: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(target))
