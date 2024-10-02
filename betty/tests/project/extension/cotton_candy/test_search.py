from pathlib import Path

import pytest

from betty.ancestry.file import File
from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.app import App
from betty.job import Context
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.extension.cotton_candy.search import Index


class TestIndex:
    async def test_build_empty(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    async def test_build_person_without_names(self, new_temporary_app: App) -> None:
        person_id = "P1"
        person = Person(id=person_id)

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    async def test_build_private_person(self, new_temporary_app: App) -> None:
        person_id = "P1"
        individual_name = "Jane"
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=individual_name,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/P1/index.html", "nl-NL"),
            ("/en/person/P1/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_name(
        self, expected: str, locale: str, new_temporary_app: App
    ) -> None:
        person_id = "P1"
        individual_name = "Jane"
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                localizers = await project.localizers
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    await localizers.get(locale),
                ).build()

                assert actual[0].text == {"jane"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/P1/index.html", "nl-NL"),
            ("/en/person/P1/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_affiliation_name(
        self, expected: str, locale: str, new_temporary_app: App
    ) -> None:
        person_id = "P1"
        affiliation_name = "Doughnut"
        person = Person(id=person_id)
        PersonName(
            person=person,
            affiliation=affiliation_name,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                localizers = await project.localizers
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    await localizers.get(locale),
                ).build()

                assert actual[0].text == {"doughnut"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/P1/index.html", "nl-NL"),
            ("/en/person/P1/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_and_affiliation_names(
        self, expected: str, locale: str, new_temporary_app: App
    ) -> None:
        person_id = "P1"
        individual_name = "Jane"
        affiliation_name = "Doughnut"
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
            affiliation=affiliation_name,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                localizers = await project.localizers
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    await localizers.get(locale),
                ).build()

                assert actual[0].text == {"jane", "doughnut"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/place/P1/index.html", "nl-NL"),
            ("/en/place/P1/index.html", "en-US"),
        ],
    )
    async def test_build_place(
        self, expected: str, locale: str, new_temporary_app: App
    ) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
            names=[
                Name(
                    {
                        "en": "Netherlands",
                        "nl": "Nederland",
                    }
                ),
            ],
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(place)
            async with project:
                localizers = await project.localizers
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    await localizers.get(locale),
                ).build()

                assert actual[0].text == {"netherlands", "nederland"}
                assert expected in actual[0].result

    async def test_build_private_place(self, new_temporary_app: App) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
            names=[
                Name({"en": "Netherlands"}),
            ],
            private=True,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.ancestry.add(place)
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    async def test_build_file_without_description(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(file)
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/file/F1/index.html", "nl-NL"),
            ("/en/file/F1/index.html", "en-US"),
        ],
    )
    async def test_build_file(
        self, expected: str, locale: str, new_temporary_app: App
    ) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(file)
            async with project:
                localizers = await project.localizers
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    await localizers.get(locale),
                ).build()

                assert actual[0].text == {
                    '"file"',
                    "is",
                    "dutch",
                    "for",
                    '"traffic',
                    'jam"',
                }
                assert expected in actual[0].result

    async def test_build_private_file(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
            private=True,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.locales["en-US"].alias = "en"
            project.ancestry.add(file)
            async with project:
                actual = await Index(
                    project.ancestry,
                    await project.jinja2_environment,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []
