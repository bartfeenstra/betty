from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.entities.file import File
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.extensions._theme.search import Index
from betty.extensions.raspberry_mint import RaspberryMint
from betty.job import Context
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.project import Project, ProjectLocale
from betty.test_utils.conftest import IsolatedProjectFactory


class TestIndex:
    @pytest.fixture
    async def dummy_project(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> AsyncIterator[Project]:
        async with isolated_project_factory(
            locales=(
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
            ),
            extensions=[RaspberryMint],
        ) as project:
            yield project

    async def test_build_empty(self, dummy_project: Project) -> None:
        actual = await Index(dummy_project, Context(), default_localizer).build()
        assert actual == []

    async def test_build_person_without_names(self, dummy_project: Project) -> None:
        person = Person(id="my-first-person")
        dummy_project.ancestry.add(person)
        actual = await Index(dummy_project, Context(), default_localizer).build()
        assert actual[0].text == {"my-first-person"}

    async def test_build_private_person(self, dummy_project: Project) -> None:
        individual_name = "Jane"
        person = Person(
            id="my-first-person",
            privacy=Privacy.PRIVATE,
        )
        PersonName(
            person=person,
            individual=individual_name,
        )
        dummy_project.ancestry.add(person)
        actual = await Index(dummy_project, Context(), default_localizer).build()
        assert actual == []

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/my-first-person/index.html", "nl-NL"),
            ("/en/person/my-first-person/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_name(
        self, expected: str, locale: str, dummy_project: Project
    ) -> None:
        individual_name = "Jane"
        person = Person(id="my-first-person")
        PersonName(
            person=person,
            individual=individual_name,
        )
        dummy_project.ancestry.add(person)
        localizers = await dummy_project.localizers
        actual = await Index(dummy_project, Context(), localizers.get(locale)).build()
        assert actual[0].text == {"my-first-person", "jane"}
        assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/my-first-person/index.html", "nl-NL"),
            ("/en/person/my-first-person/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_affiliation_name(
        self, expected: str, locale: str, dummy_project: Project
    ) -> None:
        affiliation_name = "Doughnut"
        person = Person(id="my-first-person")
        PersonName(
            person=person,
            affiliation=affiliation_name,
        )
        dummy_project.ancestry.add(person)
        localizers = await dummy_project.localizers
        actual = await Index(
            dummy_project,
            Context(),
            localizers.get(locale),
        ).build()
        assert actual[0].text == {"my-first-person", "doughnut"}
        assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/my-first-person/index.html", "nl-NL"),
            ("/en/person/my-first-person/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_and_affiliation_names(
        self, expected: str, locale: str, dummy_project: Project
    ) -> None:
        individual_name = "Jane"
        affiliation_name = "Doughnut"
        person = Person(id="my-first-person")
        PersonName(
            person=person,
            individual=individual_name,
            affiliation=affiliation_name,
        )
        dummy_project.ancestry.add(person)
        localizers = await dummy_project.localizers
        actual = await Index(dummy_project, Context(), localizers.get(locale)).build()
        assert actual[0].text == {"my-first-person", "jane", "doughnut"}
        assert expected in actual[0].result

    @pytest.mark.parametrize(
        ("expected_result", "expected_text", "locale"),
        [
            (
                "/nl/place/my-first-place/index.html",
                {"my-first-place", "nederland"},
                "nl-NL",
            ),
            (
                "/en/place/my-first-place/index.html",
                {"my-first-place", "netherlands"},
                "en-US",
            ),
        ],
    )
    async def test_build_place(
        self,
        expected_result: str,
        expected_text: set[str],
        locale: str,
        dummy_project: Project,
    ) -> None:
        place = Place(
            id="my-first-place",
            names=[
                PlaceName(
                    {
                        "en": "Netherlands",
                        "nl": "Nederland",
                    },  # ty:ignore[invalid-argument-type]
                ),
            ],
        )
        dummy_project.ancestry.add(place)
        localizers = await dummy_project.localizers
        actual = await Index(dummy_project, Context(), localizers.get(locale)).build()
        assert actual[0].text == expected_text
        assert expected_result in actual[0].result

    async def test_build_private_place(self, dummy_project: Project) -> None:
        place = Place(
            id="my-first-place",
            names=[
                PlaceName(
                    {"en": "Netherlands"},  # ty:ignore[invalid-argument-type]
                ),
            ],
            privacy=Privacy.PRIVATE,
        )
        dummy_project.ancestry.add(place)
        actual = await Index(
            dummy_project,
            Context(),
            default_localizer,
        ).build()
        assert actual == []

    @pytest.mark.parametrize(
        ("expected_text", "expected_result", "description", "locale"),
        [
            (
                {
                    Path(__file__).name,
                    "my-first-file",
                    '"file"',
                    "is",
                    "dutch",
                    "for",
                    '"traffic',
                    'jam"',
                },
                "/nl/file/my-first-file/index.html",
                '"file" is Dutch for "traffic jam"',
                "nl-NL",
            ),
            (
                {
                    Path(__file__).name,
                    "my-first-file",
                    '"file"',
                    "is",
                    "dutch",
                    "for",
                    '"traffic',
                    'jam"',
                },
                "/en/file/my-first-file/index.html",
                '"file" is Dutch for "traffic jam"',
                "en-US",
            ),
            (
                {
                    Path(__file__).name,
                    "my-first-file",
                },
                "/nl/file/my-first-file/index.html",
                None,
                "nl-NL",
            ),
            (
                {
                    Path(__file__).name,
                    "my-first-file",
                },
                "/en/file/my-first-file/index.html",
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
        dummy_project: Project,
    ) -> None:
        file = File(
            id="my-first-file",
            path=__file__,
            description=description,
        )
        dummy_project.ancestry.add(file)
        localizers = await dummy_project.localizers
        actual = await Index(
            dummy_project,
            Context(),
            localizers.get(locale),
        ).build()
        assert actual[0].text == expected_text
        assert expected_result in actual[0].result

    async def test_build_private_file(self, dummy_project: Project) -> None:
        file = File(
            id="my-first-file",
            path=__file__,
            description='"file" is Dutch for "traffic jam"',
            privacy=Privacy.PRIVATE,
        )
        dummy_project.ancestry.add(file)
        actual = await Index(
            dummy_project,
            Context(),
            default_localizer,
        ).build()
        assert actual == []
