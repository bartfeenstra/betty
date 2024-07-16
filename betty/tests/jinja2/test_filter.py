from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING

import pytest
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.date import Datey, Date, DateRange

from betty.media_type import MediaType
from betty.model.ancestry import File, FileReference, Dated, PlaceName
from betty.tests import TemplateTestCase
from betty.tests.jinja2.test___init__ import DummyHasFileReferencesEntity

if TYPE_CHECKING:
    from betty.locale.localized import Localized


class TestFilterFile(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "template", "file"),
        [
            (
                "/file/F1/file/test_filter.py",
                "{{ file | file }}",
                File(
                    id="F1",
                    path=Path(__file__),
                ),
            ),
            (
                "/file/F1/file/test_filter.py:/file/F1/file/test_filter.py",
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


class TestFilterImageResizeCover(TemplateTestCase):
    image_path = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"

    @pytest.mark.parametrize(
        ("expected", "template", "filey"),
        [
            (
                "/file/F1-99x-.png",
                "{{ filey | filter_image_resize_cover((99, none)) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1--x99.png",
                "{{ filey | filter_image_resize_cover((none, 99)) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99.png",
                "{{ filey | filter_image_resize_cover((99, 99)) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99-1x2x3x4.png",
                "{{ filey | filter_image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99.png:/file/F1-99x99.png",
                "{{ filey | filter_image_resize_cover((99, 99)) }}:{{ filey | filter_image_resize_cover((99, 99)) }}",
                File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("image/png"),
                ),
            ),
            (
                "/file/F1-99x99.png",
                "{{ filey | filter_image_resize_cover((99, 99)) }}",
                FileReference(
                    DummyHasFileReferencesEntity(),
                    File(
                        id="F1",
                        path=image_path,
                        media_type=MediaType("image/png"),
                    ),
                ),
            ),
            (
                "/file/F1-99x99-0x0x9x9.png",
                "{{ filey | filter_image_resize_cover((99, 99)) }}",
                FileReference(
                    DummyHasFileReferencesEntity(),
                    File(
                        id="F1",
                        path=image_path,
                        media_type=MediaType("image/png"),
                    ),
                    focus=(0, 0, 9, 9),
                ),
            ),
        ],
    )
    async def test(self, expected: str, template: str, filey: File) -> None:
        async with self._render(
            template_string=template,
            data={
                "filey": filey,
            },
        ) as (actual, project):
            assert expected == actual
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()


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


class TestFilterFormatDatey(TemplateTestCase):
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
