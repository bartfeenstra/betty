from typing import Any
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Person, Event, Place, File, Source, Citation, Identifiable
from betty.config import Configuration
from betty.url import DelegatingUrlGenerator, PathUrlGenerator, IdentifiableUrlGenerator


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
        self.assertEquals(expected, sut.generate(resource, True))


class IdentifiableUrlGeneratorTest(TestCase):
    def test_generate(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = IdentifiableUrlGenerator(configuration, 'prefix/%s/index.html')
        self.assertEquals('/prefix/I1/index.html',
                          sut.generate(Identifiable('I1')))

    def test_generate_with_clean_urls(self):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = IdentifiableUrlGenerator(configuration, 'prefix/%s/index.html')
        self.assertEquals('/prefix/I1/', sut.generate(Identifiable('I1')))


class DelegatingUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/index.html'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Event.Type.DEATH)),
        ('/place/P1/index.html', Place('P1', 'Place 1')),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1')),
    ])
    def test_generate(self, expected: str, resource: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = DelegatingUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))
