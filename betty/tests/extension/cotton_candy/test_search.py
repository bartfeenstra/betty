from pathlib import Path

import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.extension.cotton_candy.search import Index
from betty.locale import DEFAULT_LOCALIZER
from betty.model.ancestry import Person, Place, PlaceName, PersonName, File
from betty.project import LocaleConfiguration
from betty.task import Context


class TestIndex:
    async def test_empty(self) -> None:
        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        indexed = [item for item in await Index(app, Context(), DEFAULT_LOCALIZER).build()]

        assert [] == indexed

    async def test_person_without_names(self) -> None:
        person_id = 'P1'
        person = Person(id=person_id)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(person)
        indexed = [item for item in await Index(app, Context(), DEFAULT_LOCALIZER).build()]

        assert [] == indexed

    async def test_private_person(self) -> None:
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=individual_name,
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(person)
        indexed = [item for item in await Index(app, Context(), DEFAULT_LOCALIZER).build()]

        assert [] == indexed

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    async def test_person_with_individual_name(self, expected: str, locale: str) -> None:
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(person)
        indexed = [item for item in await Index(app, Context(), app.localizers[locale]).build()]

        assert 'jane' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    async def test_person_with_affiliation_name(self, expected: str, locale: str) -> None:
        person_id = 'P1'
        affiliation_name = 'Doughnut'
        person = Person(id=person_id)
        PersonName(
            person=person,
            affiliation=affiliation_name,
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(person)
        indexed = [item for item in await Index(app, Context(), app.localizers[locale]).build()]

        assert 'doughnut' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    async def test_person_with_individual_and_affiliation_names(self, expected: str, locale: str) -> None:
        person_id = 'P1'
        individual_name = 'Jane'
        affiliation_name = 'Doughnut'
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
            affiliation=affiliation_name,
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(person)
        indexed = [item for item in await Index(app, Context(), app.localizers[locale]).build()]

        assert 'jane doughnut' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/place/P1/index.html', 'nl-NL'),
        ('/en/place/P1/index.html', 'en-US'),
    ])
    async def test_place(self, expected: str, locale: str) -> None:
        place_id = 'P1'
        place = Place(
            id=place_id,
            names=[
                PlaceName(
                    name='Netherlands',
                    locale='en',
                ),
                PlaceName(
                    name='Nederland',
                    locale='nl',
                ),
            ],
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(place)
        indexed = [item for item in await Index(app, Context(), app.localizers[locale]).build()]

        assert 'netherlands nederland' == indexed[0]['text']
        assert expected in indexed[0]['result']

    async def test_file_without_description(self) -> None:
        file_id = 'F1'
        file = File(
            id=file_id,
            path=Path(__file__),
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(file)
        indexed = [item for item in await Index(app, Context(), DEFAULT_LOCALIZER).build()]

        assert [] == indexed

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/file/F1/index.html', 'nl-NL'),
        ('/en/file/F1/index.html', 'en-US'),
    ])
    async def test_file(self, expected: str, locale: str) -> None:
        file_id = 'F1'
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
        )

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        app.project.ancestry.add(file)
        indexed = [item for item in await Index(app, Context(), app.localizers[locale]).build()]

        assert '"file" is dutch for "traffic jam"' == indexed[0]['text']
        assert expected in indexed[0]['result']
