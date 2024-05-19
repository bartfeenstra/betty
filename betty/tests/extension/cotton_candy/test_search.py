from pathlib import Path

import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.extension.cotton_candy.search import Index
from betty.job import Context
from betty.locale import DEFAULT_LOCALIZER
from betty.model.ancestry import Person, Place, PlaceName, PersonName, File
from betty.project import LocaleConfiguration


class TestIndex:
    async def test_build_empty(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed

    async def test_build_person_without_names(self, new_temporary_app: App) -> None:
        person_id = "P1"
        person = Person(id=person_id)

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(person)
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed

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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(person)
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed

    @pytest.mark.parametrize(
        "expected, locale",
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(person)
        indexed = [
            item
            async for item in Index(
                new_temporary_app,
                Context(),
                await new_temporary_app.localizers.get(locale),
            ).build()
        ]

        assert "jane" == indexed[0]["text"]
        assert expected in indexed[0]["result"]

    @pytest.mark.parametrize(
        "expected, locale",
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(person)
        indexed = [
            item
            async for item in Index(
                new_temporary_app,
                Context(),
                await new_temporary_app.localizers.get(locale),
            ).build()
        ]

        assert "doughnut" == indexed[0]["text"]
        assert expected in indexed[0]["result"]

    @pytest.mark.parametrize(
        "expected, locale",
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(person)
        indexed = [
            item
            async for item in Index(
                new_temporary_app,
                Context(),
                await new_temporary_app.localizers.get(locale),
            ).build()
        ]

        assert "jane doughnut" == indexed[0]["text"]
        assert expected in indexed[0]["result"]

    @pytest.mark.parametrize(
        "expected, locale",
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(place)
        indexed = [
            item
            async for item in Index(
                new_temporary_app,
                Context(),
                await new_temporary_app.localizers.get(locale),
            ).build()
        ]

        assert "netherlands nederland" == indexed[0]["text"]
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.ancestry.add(place)
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed

    async def test_build_file_without_description(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
        )

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(file)
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed

    @pytest.mark.parametrize(
        "expected, locale",
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

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        new_temporary_app.project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        new_temporary_app.project.ancestry.add(file)
        indexed = [
            item
            async for item in Index(
                new_temporary_app,
                Context(),
                await new_temporary_app.localizers.get(locale),
            ).build()
        ]

        assert '"file" is dutch for "traffic jam"' == indexed[0]["text"]
        assert expected in indexed[0]["result"]

    async def test_build_private_file(self, new_temporary_app: App) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
            private=True,
        )

        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        new_temporary_app.project.configuration.locales["en-US"].alias = "en"
        app.project.ancestry.add(file)
        indexed = [
            item
            async for item in Index(
                new_temporary_app, Context(), DEFAULT_LOCALIZER
            ).build()
        ]

        assert [] == indexed
