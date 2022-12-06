from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from betty.app import App
from betty.locale import Localey
from betty.model import UserFacingEntity, Entity
from betty.model.ancestry import Person, Place, File, Source, PlaceName, Event, Citation
from betty.model.event_type import Death
from betty.project import LocaleConfiguration
from betty.url import ContentNegotiationPathUrlGenerator, _EntityUrlGenerator, AppUrlGenerator


class TestLocalizedPathUrlGenerator:
    @pytest.mark.parametrize('expected, resource', [
        ('', '/'),
        ('/index.html', '/index.html'),
        ('/example', 'example'),
        ('/example', '/example'),
        ('/example', 'example/'),
        ('/example', '/example/'),
        ('/example/index.html', 'example/index.html'),
        ('/example/index.html', '/example/index.html'),
    ])
    def test_generate(self, expected: str, resource: str):
        with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            assert expected == sut.generate(resource, 'text/html')

    @pytest.mark.parametrize('expected, resource', [
        ('', 'index.html'),
        ('', '/index.html'),
        ('/example', 'example/index.html'),
        ('/example', '/example/index.html'),
    ])
    def test_generate_with_clean_urls(self, expected: str, resource: str):
        with App() as app:
            app.project.configuration.clean_urls = True
            sut = ContentNegotiationPathUrlGenerator(app)
            assert expected == sut.generate(resource, 'text/html')

    @pytest.mark.parametrize('expected, resource', [
        ('https://example.com', '/'),
        ('https://example.com/example', 'example'),
    ])
    def test_generate_absolute(self, expected: str, resource: str):
        with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            assert expected == sut.generate(resource, 'text/html', absolute=True)

    def test_generate_with_invalid_value(self):
        with App() as app:
            sut = ContentNegotiationPathUrlGenerator(app)
            with pytest.raises(ValueError):
                sut.generate(9, 'text/html')

    @pytest.mark.parametrize('expected, app_locale, url_generator_locale', [
        ('/nl/index.html', 'nl', None),
        ('/en/index.html', 'en', None),
        ('/nl/index.html', None, 'nl'),
        ('/en/index.html', None, 'en'),
    ])
    def test_generate_multilingual(self, expected: str, app_locale: Localey | None, url_generator_locale: Localey | None):
        app = App(locale=app_locale)
        app.project.configuration.locales.replace(
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('en-US', 'en'),
        )
        sut = ContentNegotiationPathUrlGenerator(app)
        assert expected == sut.generate('/index.html', 'text/html', locale=url_generator_locale)


class EntityUrlGeneratorTestUrlyEntity(UserFacingEntity, Entity):
    pass


class EntityUrlGeneratorTestNonUrlyEntity(UserFacingEntity, Entity):
    pass


class TestEntityUrlGenerator:
    def test_generate(self):
        with App() as app:
            sut = _EntityUrlGenerator(app, EntityUrlGeneratorTestUrlyEntity)
            assert '/betty.tests.test_url.-entity-url-generator-test-urly-entity/I1/index.html' == sut.generate(EntityUrlGeneratorTestUrlyEntity('I1'), 'text/html')

    def test_generate_with_invalid_value(self):
        with App() as app:
            sut = _EntityUrlGenerator(app, EntityUrlGeneratorTestUrlyEntity)
            with pytest.raises(ValueError):
                sut.generate(EntityUrlGeneratorTestNonUrlyEntity(), 'text/html')


class TestAppUrlGenerator:
    @pytest.mark.parametrize('expected, resource', [
        ('/index.html', '/index.html'),
        ('/person/P1/index.html', Person('P1')),
        ('/event/E1/index.html', Event('E1', Death)),
        ('/place/P1/index.html', Place('P1', [PlaceName('Place 1')])),
        ('/file/F1/index.html', File('F1', Path('/tmp'))),
        ('/source/S1/index.html', Source('S1', 'Source 1')),
        ('/citation/C1/index.html', Citation('C1', Source('Source 1'))),
    ])
    def test_generate(self, expected: str, resource: Any):
        with App() as app:
            sut = AppUrlGenerator(app)
            assert expected == sut.generate(resource, 'text/html')

    def test_generate_with_invalid_value(self):
        with App() as app:
            sut = AppUrlGenerator(app)
            with pytest.raises(ValueError):
                sut.generate(9, 'text/html')
