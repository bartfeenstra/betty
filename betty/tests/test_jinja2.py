from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any, TYPE_CHECKING

import aiofiles
import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider
from betty.locale import Date, Datey, DateRange, Localized
from betty.media_type import MediaType
from betty.model import get_entity_type_name, Entity
from betty.model.ancestry import (
    File,
    PlaceName,
    Subject,
    Attendee,
    Witness,
    Dated,
    Person,
    Place,
    Citation,
)
from betty.project import Project
from betty.tests import TemplateTestCase

if TYPE_CHECKING:
    from betty.app import App


class TestJinja2Provider:
    async def test_globals(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.globals, dict)

    async def test_filters(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.filters, dict)


class TestJinja2Renderer:
    async def test_render_file(self, new_temporary_app: App) -> None:
        project = Project(new_temporary_app)
        async with project:
            sut = Jinja2Renderer(project.jinja2_environment, project.configuration)
            template = "{% if true %}true{% endif %}"
            expected_output = "true"
            async with TemporaryDirectory() as working_directory_path_str:
                working_directory_path = Path(working_directory_path_str)
                template_file_path = working_directory_path / "betty.txt.j2"
                async with aiofiles.open(template_file_path, "w") as f:
                    await f.write(template)
                await sut.render_file(template_file_path)
                async with aiofiles.open(working_directory_path / "betty.txt") as f:
                    assert expected_output == (await f.read()).strip()
                assert not template_file_path.exists()


class TestFilterFlatten(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("", '{{ [] | flatten | join(", ") }}'),
            ("", '{{ [[], [], []] | flatten | join(", ") }}'),
            (
                "kiwi, apple, banana",
                '{{ [["kiwi"], ["apple"], ["banana"]] | flatten | join(", ") }}',
            ),
        ],
    )
    async def test(self, expected: str, template: str) -> None:
        async with self._render(template_string=template) as (actual, _):
            assert expected == actual


class TestFilterParagraphs(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("<p></p>", '{{ "" | paragraphs }}'),
            (
                "<p>Apples <br>\n and <br>\n oranges</p>",
                '{{ "Apples \n and \n oranges" | paragraphs }}',
            ),
        ],
    )
    async def test(self, expected: str, template: str) -> None:
        async with self._render(template_string=template) as (actual, _):
            assert expected == actual


class TestFilterFormatDegrees(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("0° 0&#39; 0&#34;", "{{ 0 | format_degrees }}"),
            ("52° 22&#39; 1&#34;", "{{ 52.367 | format_degrees }}"),
        ],
    )
    async def test(self, expected: str, template: str) -> None:
        async with self._render(template_string=template) as (actual, _):
            assert expected == actual


class TestFilterUnique(TemplateTestCase):
    async def test(self) -> None:
        data: list[Any] = [
            999,
            {},
            999,
            {},
        ]
        async with self._render(
            template_string='{{ data | unique | join(", ") }}',
            data={
                "data": data,
            },
        ) as (actual, _):
            assert "999 == {}", actual


class TestFilterMap(TemplateTestCase):
    class MapData:
        def __init__(self, label: str):
            self.label = label

    @pytest.mark.parametrize(
        ("expected", "template", "data"),
        [
            (
                "kiwi, apple, banana",
                '{{ data | map(attribute="label") | join(", ") }}',
                [MapData("kiwi"), MapData("apple"), MapData("banana")],
            ),
            (
                "kiwi, None, apple, None, banana",
                '{% macro print_string(value) %}{% if value is none %}None{% else %}{{ value }}{% endif %}{% endmacro %}{{ ["kiwi", None, "apple", None, "banana"] | map(print_string) | join(", ") }}',
                {},
            ),
        ],
    )
    async def test(self, expected: str, template: str, data: MapData) -> None:
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual


class TestFilterFile(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "template", "file"),
        [
            (
                "/file/F1/file/test_jinja2.py",
                "{{ file | file }}",
                File(
                    id="F1",
                    path=Path(__file__),
                ),
            ),
            (
                "/file/F1/file/test_jinja2.py:/file/F1/file/test_jinja2.py",
                "{{ file | file }}:{{ file | file }}",
                File(
                    id="F1",
                    path=Path(__file__),
                ),
            ),
        ],
    )
    async def test(self, expected: str, template: str, file: File) -> None:
        async with self._render(
            template_string=template,
            data={
                "file": file,
            },
        ) as (actual, project):
            assert expected == actual
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()


class TestFilterImage(TemplateTestCase):
    image_path = (
        Path(__file__).parents[1] / "assets" / "public" / "static" / "betty-512x512.png"
    )

    @pytest.mark.parametrize(
        ("expected", "template", "file"),
        [
            (
                "/file/F1-99x-.png",
                "{{ file | image(width=99) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1--x99.png",
                "{{ file | image(height=99) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99.png",
                "{{ file | image(width=99, height=99) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99.png:/file/F1-99x99.png",
                "{{ file | image(width=99, height=99) }}:{{ file | image(width=99, height=99) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
        ],
    )
    async def test(self, expected: str, template: str, file: File) -> None:
        async with self._render(
            template_string=template,
            data={
                "file": file,
            },
        ) as (actual, project):
            assert expected == actual
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    async def test_without_width(self) -> None:
        file = File(
            id="F1",
            path=self.image_path,
            media_type=MediaType("image/png"),
        )
        with pytest.raises(ValueError):  # noqa PT011
            async with self._render(
                template_string="{{ file | image }}",
                data={
                    "file": file,
                },
            ):
                pass


class TestGlobalCiter(TemplateTestCase):
    async def test_cite(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        assert sut.cite(citation1) == 1
        assert sut.cite(citation2) == 2
        assert sut.cite(citation1) == 1

    async def test_iter(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert [(1, citation1), (2, citation2)] == list(sut)

    async def test_len(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert len(sut) == 2


class TestFormatDatey(TemplateTestCase):
    async def test(self) -> None:
        template = "{{ date | format_datey }}"
        date = Date(1970, 1, 1)
        async with self._render(
            template_string=template,
            data={
                "date": date,
            },
        ) as (actual, _):
            assert "January 1 == 1970", actual


class TestFilterSortLocalizeds(TemplateTestCase):
    class WithLocalizedNames:
        def __init__(self, identifier: str, names: list[PlaceName]):
            self.id = identifier
            self.names = names

        def __repr__(self) -> str:
            return self.id

    async def test(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        data = [
            self.WithLocalizedNames(
                "third",
                [
                    PlaceName(
                        name="3",
                        locale="nl-NL",
                    ),
                ],
            ),
            self.WithLocalizedNames(
                "second",
                [
                    PlaceName(
                        name="2",
                        locale="en",
                    ),
                    PlaceName(
                        name="1",
                        locale="nl-NL",
                    ),
                ],
            ),
            self.WithLocalizedNames(
                "first",
                [
                    PlaceName(
                        name="2",
                        locale="nl-NL",
                    ),
                    PlaceName(
                        name="1",
                        locale="en-US",
                    ),
                ],
            ),
        ]
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert "[first == second, third]", actual

    async def test_with_empty_iterable(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        async with self._render(
            template_string=template,
            data={
                "data": [],
            },
        ) as (actual, _):
            assert actual == "[]"


class TestFilterSelectLocalizeds(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "locale", "data"),
        [
            ("", "en", []),
            (
                "Apple",
                "en",
                [
                    PlaceName(
                        name="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "Apple",
                "en",
                [
                    PlaceName(
                        name="Apple",
                        locale="en-US",
                    )
                ],
            ),
            (
                "Apple",
                "en-US",
                [
                    PlaceName(
                        name="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "",
                "nl",
                [
                    PlaceName(
                        name="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "",
                "nl-NL",
                [
                    PlaceName(
                        name="Apple",
                        locale="en",
                    )
                ],
            ),
        ],
    )
    async def test(self, expected: str, locale: str, data: Iterable[Localized]) -> None:
        template = '{{ data | select_localizeds | map(attribute="name") | join(", ") }}'

        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
            locale=locale,
        ) as (actual, _):
            assert expected == actual

    async def test_include_unspecified(self) -> None:
        template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="name") | join(", ") }}'
        data = [
            PlaceName(
                name="Apple",
                locale="zxx",
            ),
            PlaceName(
                name="Apple",
                locale="und",
            ),
            PlaceName(
                name="Apple",
                locale="mul",
            ),
            PlaceName(
                name="Apple",
                locale="mis",
            ),
            PlaceName(
                name="Apple",
            ),
        ]

        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
            locale="en-US",
        ) as (actual, _):
            assert "Apple == Apple, Apple, Apple, Apple", actual


class TestFilterSelectDateds(TemplateTestCase):
    class DatedDummy(Dated):
        def __init__(self, value: str, date: Datey | None = None):
            super().__init__(date=date)
            self._value = value

        def __str__(self) -> str:
            return self._value

    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            (
                "Apple",
                {
                    "dateds": [
                        DatedDummy("Apple"),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        DatedDummy("Apple"),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        DatedDummy("Apple"),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "",
                {
                    "dateds": [
                        DatedDummy("Apple", Date(1970, 1, 1)),
                    ],
                    "date": None,
                },
            ),
            (
                "",
                {
                    "dateds": [
                        DatedDummy("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        DatedDummy("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "Apple, Strawberry",
                {
                    "dateds": [
                        DatedDummy("Apple", Date(1971, 1, 1)),
                        DatedDummy("Strawberry", Date(1970, 1, 1)),
                        DatedDummy("Banana", Date(1969, 1, 1)),
                        DatedDummy("Orange", Date(1972, 12, 31)),
                    ],
                    "date": DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
                },
            ),
        ],
    )
    async def test(self, expected: str, data: dict[str, Any]) -> None:
        template = '{{ dateds | select_dateds(date=date) | join(", ") }}'
        async with self._render(template_string=template, data=data) as (actual, _):
            assert expected == actual


class TestTestSubjectRole(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Subject()),
            ("false", Subject),
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: dict[str, Any]) -> None:
        template = "{% if data is subject_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual


class TestTestWitnessRole(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Witness()),
            ("false", Witness),
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: dict[str, Any]) -> None:
        template = "{% if data is witness_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual


class TestTestEntity(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "entity_type", "data"),
        [
            ("true", Person, Person(id="P1")),
            (
                "false",
                Person,
                Place(
                    id="P1",
                    names=[PlaceName(name="The Place")],
                ),
            ),
            (
                "true",
                Place,
                Place(
                    id="P1",
                    names=[PlaceName(name="The Place")],
                ),
            ),
            ("false", Place, Person(id="P1")),
            ("false", Place, 999),
            ("false", Person, object()),
        ],
    )
    async def test(
        self, expected: str, entity_type: type[Entity], data: dict[str, Any]
    ) -> None:
        template = f'{{% if data is entity("{get_entity_type_name(entity_type)}") %}}true{{% else %}}false{{% endif %}}'
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual
