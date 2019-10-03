from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Person, Event, Place, File, Source, Citation, Identifiable
from betty.config import Configuration
from betty.url import UrlGenerator


class UrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/'),
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example/index.html', 'example/'),
        ('/example/index.html', '/example/'),
    ])
    def test_generate_for_string_resource(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('https://example.com/index.html', '/'),
        ('https://example.com/example', 'example'),
        ('https://example.com/example', '/example'),
        ('https://example.com/example/index.html', 'example/'),
        ('https://example.com/example/index.html', '/example/'),
    ])
    def test_generate_for_string_resource_absolute(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, True))

    @parameterized.expand([
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Event.Type.DEATH)),
        ('/place/P1/index.html', Place('P1', 'Place 1')),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1')),
    ])
    def test_generate_for_identifiable_resource(self, expected: str, resource: Identifiable):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('/', '/'),
        ('/person/P1/', Person('P1')),
        ('/event/E1/', Event('E1', Event.Type.DEATH)),
        ('/place/P1/', Place('P1', 'Place 1')),
        ('/file/F1/', File('F1', '/tmp')),
        ('/source/S1/', Source('S1', 'Source 1')),
        ('/citation/C1/', Citation('C1')),
    ])
    def test_generate_for_identifiable_resource_with_clean_urls(self, expected: str, resource: Identifiable):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = UrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))
