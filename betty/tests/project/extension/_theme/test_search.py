from pathlib import Path

import pytest

from betty.ancestry.file import File
from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.app import App
from betty.job import Context
from betty.locale.localizable import StaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.project.extension._theme.search import Index
from betty.project.extension.raspberry_mint import RaspberryMint


class TestIndex:
    async def test_build_empty(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            async with project:
                actual = await Index(project, Context(), DEFAULT_LOCALIZER).build()

                assert actual == []

    async def test_build_person_without_names(self, temporary_app: App) -> None:
        person_id = "P1"
        person = Person(id=person_id)

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                actual = await Index(project, Context(), DEFAULT_LOCALIZER).build()

                assert actual[0].text == {"p1"}

    async def test_build_private_person(self, temporary_app: App) -> None:
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

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.locales["en-US"].alias = "en"
            project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            project.ancestry.add(person)
            async with project:
                actual = await Index(project, Context(), DEFAULT_LOCALIZER).build()

                assert actual == []

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "nl-NL"),
            ("/en/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_name(
        self, expected: str, locale: str, temporary_app: App
    ) -> None:
        person_id = "P1"
        individual_name = "Jane"
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
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
                actual = await Index(project, Context(), localizers.get(locale)).build()

                assert actual[0].text == {"p1", "jane"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "nl-NL"),
            ("/en/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_affiliation_name(
        self, expected: str, locale: str, temporary_app: App
    ) -> None:
        person_id = "P1"
        affiliation_name = "Doughnut"
        person = Person(id=person_id)
        PersonName(
            person=person,
            affiliation=affiliation_name,
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
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
                    project,
                    Context(),
                    localizers.get(locale),
                ).build()

                assert actual[0].text == {"p1", "doughnut"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "nl-NL"),
            ("/en/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_and_affiliation_names(
        self, expected: str, locale: str, temporary_app: App
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

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
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
                actual = await Index(project, Context(), localizers.get(locale)).build()

                assert actual[0].text == {"p1", "jane", "doughnut"}
                assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected_result", "expected_text", "locale"),
        [
            (
                "/nl/place/5f2b9323c39ee3c861a7b382d205c3d3/index.html",
                {"p1", "nederland"},
                "nl-NL",
            ),
            (
                "/en/place/5f2b9323c39ee3c861a7b382d205c3d3/index.html",
                {"p1", "netherlands"},
                "en-US",
            ),
        ],
    )
    async def test_build_place(
        self,
        expected_result: str,
        expected_text: set[str],
        locale: str,
        temporary_app: App,
    ) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
            names=[
                Name(
                    StaticTranslations(
                        {
                            "en": "Netherlands",
                            "nl": "Nederland",
                        }
                    )
                ),
            ],
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
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
                    project,
                    Context(),
                    localizers.get(locale),
                ).build()

                assert actual[0].text == expected_text
                assert expected_result in actual[0].result

    async def test_build_private_place(self, temporary_app: App) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
            names=[
                Name(StaticTranslations({"en": "Netherlands"})),
            ],
            private=True,
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.locales["en-US"].alias = "en"
            project.ancestry.add(place)
            async with project:
                actual = await Index(
                    project,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []

    @pytest.mark.parametrize(
        ("expected_text", "expected_result", "description", "locale"),
        [
            (
                {
                    Path(__file__).name,
                    "f1",
                    '"file"',
                    "is",
                    "dutch",
                    "for",
                    '"traffic',
                    'jam"',
                },
                "/nl/file/e1dffc8709f31a4987c8a88334107e89/index.html",
                '"file" is Dutch for "traffic jam"',
                "nl-NL",
            ),
            (
                {
                    Path(__file__).name,
                    "f1",
                    '"file"',
                    "is",
                    "dutch",
                    "for",
                    '"traffic',
                    'jam"',
                },
                "/en/file/e1dffc8709f31a4987c8a88334107e89/index.html",
                '"file" is Dutch for "traffic jam"',
                "en-US",
            ),
            (
                {
                    Path(__file__).name,
                    "f1",
                },
                "/nl/file/e1dffc8709f31a4987c8a88334107e89/index.html",
                None,
                "nl-NL",
            ),
            (
                {
                    Path(__file__).name,
                    "f1",
                },
                "/en/file/e1dffc8709f31a4987c8a88334107e89/index.html",
                None,
                "en-US",
            ),
        ],
    )
    async def test_build_file(
        self,
        expected_text: set[str],
        expected_result: str,
        description: str | None,
        locale: str,
        temporary_app: App,
    ) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description=description,
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
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
                    project,
                    Context(),
                    localizers.get(locale),
                ).build()

                assert actual[0].text == expected_text
                assert expected_result in actual[0].result

    async def test_build_private_file(self, temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
            private=True,
        )

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.locales["en-US"].alias = "en"
            project.ancestry.add(file)
            async with project:
                actual = await Index(
                    project,
                    Context(),
                    DEFAULT_LOCALIZER,
                ).build()

                assert actual == []
