from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.job import Context
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.file import File
from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.entity.place import Place
from betty.plugins.entity.place_name import PlaceName
from betty.plugins.extension._theme.search import Index
from betty.plugins.extension.raspberry_mint import RaspberryMint
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
            service_plugins=[RaspberryMint],
        ) as project:
            yield project

    async def test_build_empty(self, dummy_project: Project) -> None:
        actual = await Index(dummy_project, Context(), DEFAULT_LOCALIZER).build()
        assert actual == []

    async def test_build_person_without_names(self, dummy_project: Project) -> None:
        person_id = "P1"
        person = Person(id=person_id)
        dummy_project.ancestry.add(person)
        actual = await Index(dummy_project, Context(), DEFAULT_LOCALIZER).build()
        assert actual[0].text == {"p1"}

    async def test_build_private_person(self, dummy_project: Project) -> None:
        person_id = "P1"
        individual_name = "Jane"
        person = Person(
            id=person_id,
            privacy=Privacy.PRIVATE,
        )
        PersonName(
            person=person,
            individual=individual_name,
        )
        dummy_project.ancestry.add(person)
        actual = await Index(dummy_project, Context(), DEFAULT_LOCALIZER).build()
        assert actual == []

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("/nl/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "nl-NL"),
            ("/en/person/5f2b9323c39ee3c861a7b382d205c3d3/index.html", "en-US"),
        ],
    )
    async def test_build_person_with_individual_name(
        self, expected: str, locale: str, dummy_project: Project
    ) -> None:
        person_id = "P1"
        individual_name = "Jane"
        person = Person(id=person_id)
        PersonName(
            person=person,
            individual=individual_name,
        )
        dummy_project.ancestry.add(person)
        localizers = await dummy_project.localizers
        actual = await Index(dummy_project, Context(), localizers.get(locale)).build()
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
        self, expected: str, locale: str, dummy_project: Project
    ) -> None:
        person_id = "P1"
        affiliation_name = "Doughnut"
        person = Person(id=person_id)
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
        self, expected: str, locale: str, dummy_project: Project
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
        dummy_project.ancestry.add(person)
        localizers = await dummy_project.localizers
        actual = await Index(dummy_project, Context(), localizers.get(locale)).build()
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
        dummy_project: Project,
    ) -> None:
        place_id = "P1"
        place = Place(
            id=place_id,
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
        place_id = "P1"
        place = Place(
            id=place_id,
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
        dummy_project: Project,
    ) -> None:
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
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
        file_id = "F1"
        file = File(
            id=file_id,
            path=Path(__file__),
            description='"file" is Dutch for "traffic jam"',
            privacy=Privacy.PRIVATE,
        )
        dummy_project.ancestry.add(file)
        actual = await Index(
            dummy_project,
            Context(),
            DEFAULT_LOCALIZER,
        ).build()
        assert actual == []
