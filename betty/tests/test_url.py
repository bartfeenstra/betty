from betty.url import DelegatingUrlGenerator, PathUrlGenerator, IdentifiableUrlGenerator, AliasUrlGenerator
from betty.config import Configuration
from betty.ancestry import Person, Event, Place, File, Source, Citation, Identifiable, PlaceName
from typing import Any
from unittest import TestCase

from parameterized import parameterized


class PathUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/', '/'),
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example/', 'example/'),
        ('/example/', '/example/'),
        ('/example/index.html', 'example/index.html'),
        ('/example/index.html', '/example/index.html'),
    ])
    def test_generate(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('/example/', 'example/index.html'),
        ('/example/', '/example/index.html'),
    ])
    def test_generate_with_clean_urls(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = PathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('https://example.com/', '/'),
        ('https://example.com/example', 'example'),
    ])
    def test_generate_absolute(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, absolute=True))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathUrlGenerator(configuration)
        with self.assertRaises(ValueError):
            sut.generate(9)


class AliasUrlGeneratorTest(TestCase):
    def test_generate(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = AliasUrlGenerator(configuration, '<alias>', 'path')
        self.assertEquals('/path', sut.generate('<alias>'))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = AliasUrlGenerator(configuration, 'alias', 'path')
        with self.assertRaises(ValueError):
            sut.generate('<notalias>')


class IdentifiableUrlGeneratorTest(TestCase):
    def test_generate(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = IdentifiableUrlGenerator(
            configuration, Identifiable, 'prefix/%s/index.html')
        self.assertEquals('/prefix/I1/index.html',
                          sut.generate(Identifiable('I1')))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = IdentifiableUrlGenerator(
            configuration, Identifiable, 'prefix/%s/index.html')
        with self.assertRaises(ValueError):
            sut.generate(9)


class DelegatingUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/index.html'),
        ('/index.html', '<front>'),
        ('/person/index.html', '<person>'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/index.html', '<event>'),
        ('/event/E1/index.html', Event('E1', Event.Type.DEATH)),
        ('/place/index.html', '<place>'),
        ('/place/P1/index.html', Place('P1', [PlaceName('Place 1')])),
        ('/file/index.html', '<file>'),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/index.html', '<source>'),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/index.html', '<citation>'),
        ('/citation/C1/index.html', Citation('C1')),
    ])
    def test_generate(self, expected: str, resource: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = DelegatingUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))
