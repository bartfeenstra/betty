from typing import Any

from parameterized import parameterized

from betty.app import LocaleConfiguration, App
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
        async with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEqual(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('', 'index.html'),
        ('', '/index.html'),
        ('/example', 'example/index.html'),
        ('/example', '/example/index.html'),
    ])
    @sync
    async def test_generate_with_clean_urls(self, expected: str, resource: str):
        async with App() as app:
            app.configuration.clean_urls = True
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEqual(expected, sut.generate(resource, 'text/html'))

    @parameterized.expand([
        ('https://example.com', '/'),
        ('https://example.com/example', 'example'),
    ])
    @sync
    async def test_generate_absolute(self, expected: str, resource: str):
        async with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            self.assertEqual(expected, sut.generate(
                resource, 'text/html', absolute=True))

    @sync
    async def test_generate_with_invalid_value(self):
        async with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            with self.assertRaises(ValueError):
                sut.generate(9, 'text/html')

    @sync
    async def test_generate_multilingual(self):
        app = App()
        app.configuration.locales.replace([
            LocaleConfiguration('nl'),
            LocaleConfiguration('en'),
        ])
        async with app:
            sut = ContentNegotiationPathUrlGenerator(app)
            with app.activate_locale('nl'):
                self.assertEqual('/nl/index.html', sut.generate('/index.html', 'text/html'))
            with app.activate_locale('en'):
                self.assertEqual('/en/index.html', sut.generate('/index.html', 'text/html'))


class EntityUrlGeneratorTest(TestCase):
    class UrlyEntity(Entity):
        pass

    @sync
    async def test_generate(self):
        async with App() as app:
            sut = _EntityUrlGenerator(app, self.UrlyEntity, 'prefix/%s/index.%s')
            self.assertEqual('/prefix/I1/index.html', sut.generate(self.UrlyEntity('I1'), 'text/html'))

    @sync
    async def test_generate_with_invalid_value(self):
        async with App() as app:
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
        async with App() as app:
            sut = AppUrlGenerator(app)
            self.assertEqual(expected, sut.generate(resource, 'text/html'))

    @sync
    async def test_generate_with_invalid_value(self):
        async with App() as app:
            sut = AppUrlGenerator(app)
            with self.assertRaises(ValueError):
                sut.generate(9, 'text/html')
