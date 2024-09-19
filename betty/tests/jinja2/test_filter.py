from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING

import pytest
from betty.ancestry import (
    File,
    FileReference,
    HasFileReferences,
)
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale import (
    NO_LINGUISTIC_CONTENT,
    UNDETERMINED_LOCALE,
    MULTIPLE_LOCALES,
    UNCODED_LOCALE,
    DEFAULT_LOCALE,
)
from betty.date import Datey, Date, DateRange
from betty.locale.localizable import StaticTranslationsLocalizable
from betty.locale.localized import Localized, LocalizedStr
from betty.media_type import MediaType
from betty.test_utils.ancestry import DummyHasDate
from betty.test_utils.assets.templates import TemplateTestBase
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from collections.abc import Sequence, MutableMapping


class DummyHasFileReferencesEntity(HasFileReferences, DummyEntity):
    pass


class TestFilterFile(TemplateTestBase):
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
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()


class TestFilterFlatten(TemplateTestBase):
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
            assert actual == expected


class TestFilterParagraphs(TemplateTestBase):
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
            assert actual == expected


class TestFilterFormatDegrees(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("0° 0&#39; 0&#34;", "{{ 0 | format_degrees }}"),
            ("52° 22&#39; 1&#34;", "{{ 52.367 | format_degrees }}"),
        ],
    )
    async def test(self, expected: str, template: str) -> None:
        async with self._render(template_string=template) as (actual, _):
            assert actual == expected


class TestFilterUnique(TemplateTestBase):
    async def test(self) -> None:
        data: Sequence[Any] = [
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
            assert actual == "999, {}"


class TestFilterMap(TemplateTestBase):
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
            assert actual == expected


class TestFilterImageResizeCover(TemplateTestBase):
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
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()


class TestFilterSelectHasDates(TemplateTestBase):
    class _DummyHasDate(DummyHasDate):
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
                        _DummyHasDate("Apple"),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "",
                {
                    "dateds": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": None,
                },
            ),
            (
                "",
                {
                    "dateds": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "dateds": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "Apple, Strawberry",
                {
                    "dateds": [
                        _DummyHasDate("Apple", Date(1971, 1, 1)),
                        _DummyHasDate("Strawberry", Date(1970, 1, 1)),
                        _DummyHasDate("Banana", Date(1969, 1, 1)),
                        _DummyHasDate("Orange", Date(1972, 12, 31)),
                    ],
                    "date": DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
                },
            ),
        ],
    )
    async def test(self, expected: str, data: MutableMapping[str, Any]) -> None:
        template = '{{ dateds | select_has_dates(date=date) | join(", ") }}'
        async with self._render(template_string=template, data=data) as (actual, _):
            assert actual == expected


class DummyLocalized(Localized):
    def __init__(self, value: str, *, locale: str):
        self._locale = locale
        self.value = value


class TestFilterSelectLocalizeds(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "locale", "data"),
        [
            ("", "en", []),
            (
                "Apple",
                "en",
                [
                    DummyLocalized(
                        value="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "Apple",
                "en",
                [
                    DummyLocalized(
                        value="Apple",
                        locale="en-US",
                    )
                ],
            ),
            (
                "Apple",
                "en-US",
                [
                    DummyLocalized(
                        value="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "",
                "nl",
                [
                    DummyLocalized(
                        value="Apple",
                        locale="en",
                    )
                ],
            ),
            (
                "",
                "nl-NL",
                [
                    DummyLocalized(
                        value="Apple",
                        locale="en",
                    )
                ],
            ),
        ],
    )
    async def test(self, expected: str, locale: str, data: Iterable[Localized]) -> None:
        template = (
            '{{ data | select_localizeds | map(attribute="value") | join(", ") }}'
        )

        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
            locale=locale,
        ) as (actual, _):
            assert actual == expected

    async def test_include_unspecified(self) -> None:
        template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="value") | join(", ") }}'
        data = [
            DummyLocalized(
                value="Apple",
                locale=NO_LINGUISTIC_CONTENT,
            ),
            DummyLocalized(
                value="Apple",
                locale=UNDETERMINED_LOCALE,
            ),
            DummyLocalized(
                value="Apple",
                locale=MULTIPLE_LOCALES,
            ),
            DummyLocalized(
                value="Apple",
                locale=UNCODED_LOCALE,
            ),
        ]

        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
            locale="en-US",
        ) as (actual, _):
            assert actual == "Apple, Apple, Apple, Apple"


class TestFilterSortLocalizeds(TemplateTestBase):
    class WithLocalizedDummyLocalizeds:
        def __init__(self, identifier: str, names: Sequence[DummyLocalized]):
            self.id = identifier
            self.names = names

        def __repr__(self) -> str:
            return self.id

    async def test(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="value") }}'
        data = [
            self.WithLocalizedDummyLocalizeds(
                "third",
                [
                    DummyLocalized(
                        value="3",
                        locale="nl-NL",
                    ),
                ],
            ),
            self.WithLocalizedDummyLocalizeds(
                "second",
                [
                    DummyLocalized(
                        value="2",
                        locale="en",
                    ),
                    DummyLocalized(
                        value="1",
                        locale="nl-NL",
                    ),
                ],
            ),
            self.WithLocalizedDummyLocalizeds(
                "first",
                [
                    DummyLocalized(
                        value="2",
                        locale="nl-NL",
                    ),
                    DummyLocalized(
                        value="1",
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
            assert actual == "[first, second, third]"

    async def test_with_empty_iterable(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="value") }}'
        async with self._render(
            template_string=template,
            data={
                "data": [],
            },
        ) as (actual, _):
            assert actual == "[]"


class TestFilterFormatDatey(TemplateTestBase):
    async def test(self) -> None:
        template = "{{ date | format_datey }}"
        date = Date(1970, 1, 1)
        async with self._render(
            template_string=template,
            data={
                "date": date,
            },
        ) as (actual, _):
            assert actual == "January 1, 1970"


class TestFilterHtmlLang(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "localized_locale"),
        [
            ("Hallo, wereld!", DEFAULT_LOCALE),
            ('<span lang="nl">Hallo, wereld!</span>', "nl"),
        ],
    )
    async def test(self, expected: str, localized_locale: str) -> None:
        template = "{{ localized | html_lang }}"
        localized = LocalizedStr("Hallo, wereld!", locale=localized_locale)
        async with self._render(
            template_string=template,
            data={
                "localized": localized,
            },
        ) as (actual, _):
            assert actual == expected


class TestFilterLocalizeHtmlLang(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "localized_locale"),
        [
            ("Hallo, wereld!", DEFAULT_LOCALE),
            ('<span lang="nl">Hallo, wereld!</span>', "nl"),
        ],
    )
    async def test(self, expected: str, localized_locale: str) -> None:
        template = "{{ localizable | localize_html_lang }}"
        localizable = StaticTranslationsLocalizable(
            {
                localized_locale: "Hallo, wereld!",
            }
        )
        async with self._render(
            template_string=template,
            data={
                "localizable": localizable,
            },
        ) as (actual, _):
            assert actual == expected
