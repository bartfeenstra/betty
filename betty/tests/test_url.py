from tempfile import TemporaryDirectory
from typing import Any

from parameterized import parameterized

from betty.app import Configuration, LocaleConfiguration, App
from betty.asyncio import sync
from betty.model import Entity
from betty.model.ancestry import Person, Place, File, Source, PlaceName, Event, Citation
from betty.model.event_type import Death
from betty.tests import TestCase
from betty.url import ContentNegotiationPathUrlGenerator, _EntityUrlGenerator, AppUrlGenerator


class LocalizedPathUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('', '/'),
        ('/index.html', '/index.html'),
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example', 'example/'),
        ('/example', '/example/'),
        ('/example/index.html', 'example/index.html'),
        ('/example/index.html', '/example/index.html'),
    ])
    @sync
    async def test_generate(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        async with App(configuration) as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEquals(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('', 'index.html'),
        ('', '/index.html'),
        ('/example', 'example/index.html'),
        ('/example', '/example/index.html'),
    ])
    @sync
    async def test_generate_with_clean_urls(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.clean_urls = True
        async with App(configuration) as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEquals(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('https://example.com', '/'),
        ('https://example.com/example', 'example'),
    ])
    @sync
    async def test_generate_absolute(self, expected: str, resource: str):
        configuration = Configuration('/tmp', 'https://example.com')
        async with App(configuration) as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEquals(expected, sut.generate(
                resource, 'text/html', absolute=True))

    @sync
    async def test_generate_with_invalid_value(self):
        configuration = Configuration('/tmp', 'https://example.com')
        async with App(configuration) as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            with self.assertRaises(ValueError):
                sut.generate(9, 'text/html')

    @sync
    async def test_generate_multilingual(self):
        configuration = Configuration('/tmp', 'https://example.com')
        configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        async with App(configuration) as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            async with app.with_locale('nl'):
                self.assertEquals('/nl/index.html', sut.generate('/index.html', 'text/html'))
            async with app.with_locale('en'):
                self.assertEquals('/en/index.html', sut.generate('/index.html', 'text/html'))


class EntityUrlGeneratorTest(TestCase):
    class UrlyEntity(Entity):
        pass

    @sync
    async def test_generate(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration) as app:
                sut = _EntityUrlGenerator(app, self.UrlyEntity, 'prefix/%s/index.%s')
                self.assertEquals('/prefix/I1/index.html', sut.generate(self.UrlyEntity('I1'), 'text/html'))

    @sync
    async def test_generate_with_invalid_value(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration) as app:
                sut = _EntityUrlGenerator(app, self.UrlyEntity, 'prefix/%s/index.html')
                with self.assertRaises(ValueError):
                    sut.generate(9, 'text/html')


class AppUrlGeneratorTest(TestCase):
    @parameterized.expand([
        ('/index.html', '/index.html'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Death())),
        ('/place/P1/index.html', Place('P1', [PlaceName('Place 1')])),
        ('/file/F1/index.html', File('F1', '/tmp')),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1', Source('Source 1'))),
    ])
    @sync
    async def test_generate(self, expected: str, resource: Any):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration) as app:
                sut = AppUrlGenerator(app)
                self.assertEquals(expected, sut.generate(resource, 'text/html'))

    @sync
    async def test_generate_with_invalid_value(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration) as app:
                sut = AppUrlGenerator(app)
                with self.assertRaises(ValueError):
                    sut.generate(9, 'text/html')
