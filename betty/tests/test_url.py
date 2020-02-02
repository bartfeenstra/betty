from betty.url import PathResourceUrlGenerator, IdentifiableResourceUrlGenerator, SiteUrlGenerator
from betty.config import Configuration, LocaleConfiguration
from betty.ancestry import Person, Event, Place, File, Source, Citation, Identifiable, LocalizedName, IdentifiableEvent
from typing import Any
from unittest import TestCase

from parameterized import parameterized


class PathUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/', '/'),
        ('/index.html', '/index.html'),
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example/', 'example/'),
        ('/example/', '/example/'),
        ('/example/index.html', 'example/index.html'),
        ('/example/index.html', '/example/index.html'),
    ])
    def test_generate(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathResourceUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('/', 'index.html'),
        ('/', '/index.html'),
        ('/example/', 'example/index.html'),
        ('/example/', '/example/index.html'),
    ])
    def test_generate_with_clean_urls(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = PathResourceUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('https://example.com/', '/'),
        ('https://example.com/example', 'example'),
    ])
    def test_generate_absolute(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathResourceUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(
            resource, 'text/html', absolute=True))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = PathResourceUrlGenerator(configuration)
        with self.assertRaises(ValueError):
            sut.generate(9, 'text/html')

    def test_generate_multilingual(self):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.locales.clear()
        configuration.locales['nl'] = LocaleConfiguration('nl')
        configuration.locales['en'] = LocaleConfiguration('en')
        sut = PathResourceUrlGenerator(configuration)
        self.assertEquals('/nl/index.html',
                          sut.generate('/index.html', 'text/html'))
        self.assertEquals(
            '/en/index.html', sut.generate('/index.html', 'text/html', locale='en'))


class IdentifiableUrlGeneratorTest(TestCase):
    def test_generate(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = IdentifiableResourceUrlGenerator(
            configuration, Identifiable, 'prefix/%s/index.%s')
        self.assertEquals('/prefix/I1/index.html',
                          sut.generate(Identifiable('I1'), 'text/html'))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = IdentifiableResourceUrlGenerator(
            configuration, Identifiable, 'prefix/%s/index.html')
        with self.assertRaises(ValueError):
            sut.generate(9, 'text/html')


class SiteUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/index.html'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', IdentifiableEvent('E1', Event.Type.DEATH)),
        ('/place/P1/index.html', Place('P1', [LocalizedName('Place 1')])),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1', Source('S1', 'Source 1'))),
    ])
    def test_generate(self, expected: str, resource: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = SiteUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, 'text/html'))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = SiteUrlGenerator(configuration)
        with self.assertRaises(ValueError):
            sut.generate(9, 'text/html')
