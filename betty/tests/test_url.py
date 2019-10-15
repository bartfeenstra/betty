from betty.url import LocalizedPathUrlGenerator, IdentifiableUrlGenerator, LocalizedUrlGenerator
from betty.config import Configuration, LocaleConfiguration
from betty.ancestry import Person, Event, Place, File, Source, Citation, Identifiable, PlaceName
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
        sut = LocalizedPathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('/', 'index.html'),
        ('/', '/index.html'),
        ('/example/', 'example/index.html'),
        ('/example/', '/example/index.html'),
    ])
    def test_generate_with_clean_urls(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        sut = LocalizedPathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    @parameterized.expand([
        ('https://example.com/', '/'),
        ('https://example.com/example', 'example'),
    ])
    def test_generate_absolute(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = LocalizedPathUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource, absolute=True))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = LocalizedPathUrlGenerator(configuration)
        with self.assertRaises(ValueError):
            sut.generate(9)

    def test_generate_multilingual(self):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.locales.clear()
        configuration.locales['nl'] = LocaleConfiguration('nl')
        configuration.locales['en'] = LocaleConfiguration('en')
        sut = LocalizedPathUrlGenerator(configuration)
        self.assertEquals('/nl/index.html', sut.generate('/index.html'))
        self.assertEquals('/en/index.html',
                          sut.generate('/index.html', locale='en'))


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


class LocalizedUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/index.html'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Event.Type.DEATH)),
        ('/place/P1/index.html', Place('P1', [PlaceName('Place 1')])),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1')),
    ])
    def test_generate(self, expected: str, resource: Any):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = LocalizedUrlGenerator(configuration)
        self.assertEquals(expected, sut.generate(resource))

    def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        sut = LocalizedUrlGenerator(configuration)
        with self.assertRaises(ValueError):
            sut.generate(9)
