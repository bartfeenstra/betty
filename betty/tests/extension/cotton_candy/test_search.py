from pathlib import Path

import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.extension.cotton_candy.search import Index
from betty.job import Context
from betty.locale import DEFAULT_LOCALIZER
from betty.model.ancestry import Person, Place, PlaceName, PersonName, File
from betty.project import LocaleConfiguration, Project


class TestIndex:
    async def test_build_empty(self, new_temporary_app: App) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(CottonCandy)
        project.configuration.locales["en-US"].alias = "en"
        project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        async with project:
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []

    async def test_build_person_without_names(self, new_temporary_app: App) -> None:
        person_id = "P1"
        person = Person(id=person_id)

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []

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

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []

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

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(
                    project, Context(), await project.localizers.get(locale)
                ).build()
            ]

            assert indexed[0]["text"] == "jane"
            assert expected in indexed[0]["result"]

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

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(
                    project, Context(), await project.localizers.get(locale)
                ).build()
            ]

            assert indexed[0]["text"] == "doughnut"
            assert expected in indexed[0]["result"]

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

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(
                    project, Context(), await project.localizers.get(locale)
                ).build()
            ]

            assert indexed[0]["text"] == "jane doughnut"
            assert expected in indexed[0]["result"]

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
                PlaceName(
                    name="Netherlands",
                    locale="en",
                ),
                PlaceName(
                    name="Nederland",
                    locale="nl",
                ),
            ],
        )

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(
                    project, Context(), await project.localizers.get(locale)
                ).build()
            ]

            assert indexed[0]["text"] == "netherlands nederland"
            assert expected in indexed[0]["result"]

    async def test_build_private_place(self, new_temporary_app: App) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
            names=[
                PlaceName(
                    name="Netherlands",
                    locale="en",
                ),
            ],
            private=True,
        )

        project = Project(new_temporary_app)
        project.configuration.extensions.enable(CottonCandy)
        project.configuration.locales["en-US"].alias = "en"
        project.ancestry.add(place)
        async with project:
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []

    async def test_build_file_without_description(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
        )

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []

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

        project = Project(new_temporary_app)
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
            indexed = [
                item
                async for item in Index(
                    project, Context(), await project.localizers.get(locale)
                ).build()
            ]

            assert indexed[0]["text"] == '"file" is dutch for "traffic jam"'
            assert expected in indexed[0]["result"]

    async def test_build_private_file(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
            private=True,
        )

        project = Project(new_temporary_app)
        project.configuration.extensions.enable(CottonCandy)
        project.configuration.locales["en-US"].alias = "en"
        project.ancestry.add(file)
        async with project:
            indexed = [
                item
                async for item in Index(project, Context(), DEFAULT_LOCALIZER).build()
            ]

            assert indexed == []
