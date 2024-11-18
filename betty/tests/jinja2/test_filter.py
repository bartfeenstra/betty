from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING

import aiofiles
import pytest
from PIL import Image

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.date import Date, DateRange, Datey
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.job import Context
from betty.locale import (
    NO_LINGUISTIC_CONTENT,
    UNDETERMINED_LOCALE,
    MULTIPLE_LOCALES,
    UNCODED_LOCALE,
    DEFAULT_LOCALE,
)
from betty.locale.localizable import plain
from betty.locale.localized import Localized, LocalizedStr
from betty.media_type import MediaType
from betty.media_type.media_types import SVG
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.jinja2 import TemplateStringTestBase
from betty.test_utils.locale.localized import DummyLocalized
from betty.tests.ancestry.test___init__ import DummyHasFileReferences

if TYPE_CHECKING:
    from collections.abc import Sequence, MutableMapping


class _DummyHasDate(DummyHasDate):
    def __init__(self, value: str, date: Datey | None = None):
        super().__init__(date=date)
        self.value = value

    def __str__(self) -> str:
        return self.value


class _DummyLocalized(DummyLocalized):
    def __init__(self, value: str, locale: str):
        super().__init__(locale)
        self.value = value


class TestFilterFile(TemplateStringTestBase):
    _PARAMETER_ARGNAMES = ("expected", "template", "file")
    _PARAMETER_ARGVALUES = [
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
    ]

    @pytest.mark.parametrize(_PARAMETER_ARGNAMES, _PARAMETER_ARGVALUES)
    async def test(self, expected: str, template: str, file: File) -> None:
        async with self.assert_template_string(
            template=template,
            data={
                "file": file,
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    @pytest.mark.parametrize(_PARAMETER_ARGNAMES, _PARAMETER_ARGVALUES)
    async def test_with_job_context(
        self, expected: str, template: str, file: File
    ) -> None:
        async with self.assert_template_string(
            template=template,
            data={
                "file": file,
                "job_context": Context(),
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()


class TestFilterFlatten(TemplateStringTestBase):
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
        async with self.assert_template_string(template=template) as (actual, _):
            assert actual == expected


class TestFilterParagraphs(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "autoescape", "template"),
        [
            ("<p></p>", True, '{{ "" | paragraphs }}'),
            ("<p></p>", False, '{{ "" | paragraphs }}'),
            (
                "<p>Apples <br>\n and <br>\n oranges</p>",
                True,
                '{{ "Apples \n and \n oranges" | paragraphs }}',
            ),
            (
                "<p>Apples <br>\n and <br>\n oranges</p>",
                False,
                '{{ "Apples \n and \n oranges" | paragraphs }}',
            ),
        ],
    )
    async def test(self, expected: str, autoescape: bool, template: str) -> None:
        async with self.assert_template_string(
            template=template, autoescape=autoescape
        ) as (
            actual,
            _,
        ):
            assert actual == expected


class TestFilterFormatDegrees(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("0° 0&#39; 0&#34;", "{{ 0 | format_degrees }}"),
            ("52° 22&#39; 1&#34;", "{{ 52.367 | format_degrees }}"),
        ],
    )
    async def test(self, expected: str, template: str) -> None:
        async with self.assert_template_string(template=template) as (actual, _):
            assert actual == expected


class TestFilterUnique(TemplateStringTestBase):
    async def test(self) -> None:
        data: Sequence[Any] = [
            999,
            {},
            999,
            {},
        ]
        async with self.assert_template_string(
            template='{{ data | unique | join(", ") }}',
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == "999, {}"


class TestFilterMap(TemplateStringTestBase):
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
        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestFilterImageResizeCover(TemplateStringTestBase):
    _IMAGE_PATH = ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
    _PARAMETER_ARGNAMES = ("expected", "template", "filey")
    _PARAMETER_ARGVALUES = [
        (
            "/file/F1-99x-.png",
            "{{ filey | filter_image_resize_cover((99, none)) }}",
            File(
                id="F1",
                path=_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
        (
            "/file/F1--x99.png",
            "{{ filey | filter_image_resize_cover((none, 99)) }}",
            File(
                id="F1",
                path=_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
        (
            "/file/F1-99x99.png",
            "{{ filey | filter_image_resize_cover((99, 99)) }}",
            File(
                id="F1",
                path=_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
        (
            "/file/F1-99x99-1x2x3x4.png",
            "{{ filey | filter_image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
            File(
                id="F1",
                path=_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
        (
            "/file/F1-99x99.png:/file/F1-99x99.png",
            "{{ filey | filter_image_resize_cover((99, 99)) }}:{{ filey | filter_image_resize_cover((99, 99)) }}",
            File(
                id="F1",
                path=_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
        (
            "/file/F1-99x99.png",
            "{{ filey | filter_image_resize_cover((99, 99)) }}",
            FileReference(
                DummyHasFileReferences(),
                File(
                    id="F1",
                    path=_IMAGE_PATH,
                    media_type=MediaType("image/png"),
                ),
            ),
        ),
        (
            "/file/F1-99x99-0x0x9x9.png",
            "{{ filey | filter_image_resize_cover((99, 99)) }}",
            FileReference(
                DummyHasFileReferences(),
                File(
                    id="F1",
                    path=_IMAGE_PATH,
                    media_type=MediaType("image/png"),
                ),
                focus=(0, 0, 9, 9),
            ),
        ),
    ]

    @pytest.mark.parametrize(_PARAMETER_ARGNAMES, _PARAMETER_ARGVALUES)
    async def test(self, expected: str, template: str, filey: File) -> None:
        async with self.assert_template_string(
            template=template,
            data={
                "filey": filey,
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    @pytest.mark.parametrize(_PARAMETER_ARGNAMES, _PARAMETER_ARGVALUES)
    async def test_with_job_context(
        self, expected: str, template: str, filey: File
    ) -> None:
        async with self.assert_template_string(
            template=template,
            data={
                "filey": filey,
                "job_context": Context(),
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    async def test_with_svg(self, tmp_path: Path) -> None:
        image_path = tmp_path / "image.svg"
        async with aiofiles.open(image_path, "w") as f:
            await f.write(
                '<?xml version="1.0" encoding="UTF-8"?><svg version="1.1" xmlns="http://www.w3.org/2000/svg"></svg>'
            )
        async with self.assert_template_string(
            template="{{ filey | filter_image_resize_cover }}",
            data={
                "filey": File(
                    id="F1",
                    path=image_path,
                    media_type=SVG,
                )
            },
        ) as (actual, project):
            assert actual == "/file/F1/file/image.svg"
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    async def test_with_pdf(self, tmp_path: Path) -> None:
        image_path = tmp_path / "image.pdf"
        image = Image.new("1", (1, 1))
        image.save(image_path)
        async with self.assert_template_string(
            template="{{ filey | filter_image_resize_cover }}",
            data={
                "filey": File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("application/pdf"),
                )
            },
        ) as (actual, project):
            assert actual == "/file/F1-.jpg"
            for file_path in actual.split(":"):
                assert (
                    project.configuration.www_directory_path / file_path[1:]
                ).exists()

    async def test_with_invalid_image(self, tmp_path: Path) -> None:
        file_path = tmp_path / "not-an-image.txt"
        file_path.touch()
        with pytest.raises(ValueError):  # noqa PT011
            async with self.assert_template_string(
                template="{{ filey | filter_image_resize_cover }}",
                data={
                    "filey": File(
                        id="F1",
                        path=file_path,
                        media_type=MediaType("text/plain"),
                    )
                },
            ):
                pass  # pragma: nocover

    async def test_with_file_without_media_type(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):  # noqa PT011
            async with self.assert_template_string(
                template="{{ filey | filter_image_resize_cover }}",
                data={"filey": File(id="F1", path=self._IMAGE_PATH)},
            ):
                pass  # pragma: nocover


class TestFilterSelectHasDates(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": None,
                },
            ),
            (
                "",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "Apple, Strawberry",
                {
                    "has_dates": [
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
        template = '{{ has_dates | select_has_dates(date=date) | join(", ") }}'
        async with self.assert_template_string(template=template, data=data) as (
            actual,
            _,
        ):
            assert actual == expected


class TestFilterSelectLocalizeds(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "locale", "data"),
        [
            ("", "en", []),
            (
                "en",
                "en",
                [DummyLocalized(locale="en")],
            ),
            (
                "en-US",
                "en",
                [DummyLocalized(locale="en-US")],
            ),
            (
                "en",
                "en-US",
                [DummyLocalized(locale="en")],
            ),
            (
                "",
                "nl",
                [DummyLocalized(locale="en")],
            ),
            (
                "",
                "nl-NL",
                [DummyLocalized(locale="en")],
            ),
        ],
    )
    async def test(self, expected: str, locale: str, data: Iterable[Localized]) -> None:
        template = (
            '{{ data | select_localizeds | map(attribute="locale") | join(", ") }}'
        )

        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
            },
            locale=locale,
        ) as (actual, _):
            assert actual == expected

    async def test_include_unspecified(self) -> None:
        template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="locale") | join(", ") }}'
        data = [
            DummyLocalized(locale=NO_LINGUISTIC_CONTENT),
            DummyLocalized(locale=UNDETERMINED_LOCALE),
            DummyLocalized(locale=MULTIPLE_LOCALES),
            DummyLocalized(locale=UNCODED_LOCALE),
        ]

        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
            },
            locale="en-US",
        ) as (actual, _):
            assert actual == "zxx, und, mul, mis"


class TestFilterSortLocalizeds(TemplateStringTestBase):
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
                    _DummyLocalized("3", "nl-NL"),
                ],
            ),
            self.WithLocalizedDummyLocalizeds(
                "second",
                [
                    _DummyLocalized("2", "en"),
                    _DummyLocalized("1", "nl-NL"),
                ],
            ),
            self.WithLocalizedDummyLocalizeds(
                "first",
                [
                    _DummyLocalized("2", "nl-NL"),
                    _DummyLocalized("1", "en-US"),
                ],
            ),
        ]
        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == "[first, second, third]"

    async def test_with_empty_iterable(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="value") }}'
        async with self.assert_template_string(
            template=template,
            data={
                "data": [],
            },
        ) as (actual, _):
            assert actual == "[]"


class TestFilterFormatDatey(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ date | format_datey }}"
        date = Date(1970, 1, 1)
        async with self.assert_template_string(
            template=template,
            data={
                "date": date,
            },
        ) as (actual, _):
            assert actual == "January 1, 1970"


class TestFilterHtmlLang(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "autoescape", "localized_locale"),
        [
            ("Hallo, wereld!", True, DEFAULT_LOCALE),
            ("Hallo, wereld!", False, DEFAULT_LOCALE),
            ('<span lang="nl">Hallo, wereld!</span>', True, "nl"),
            ('<span lang="nl">Hallo, wereld!</span>', False, "nl"),
        ],
    )
    async def test(
        self, expected: str, autoescape: bool, localized_locale: str
    ) -> None:
        template = "{{ localized | html_lang }}"
        localized = LocalizedStr("Hallo, wereld!", locale=localized_locale)
        async with self.assert_template_string(
            template=template,
            data={
                "localized": localized,
            },
            autoescape=autoescape,
        ) as (actual, _):
            assert actual == expected


class TestFilterHashid(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ data | hashid }}"
        async with self.assert_template_string(
            template=template,
            data={"data": "Hello, world!"},
        ) as (actual, _):
            assert actual == "6cd3556deb0da54bca060b4c39479839"


class TestFilterJson(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ data | json }}"
        async with self.assert_template_string(
            template=template,
            data={"data": [1, 2, 3]},
        ) as (actual, _):
            assert actual == "[1, 2, 3]"


class TestFilterLocalize(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ data | localize }}"
        async with self.assert_template_string(
            template=template,
            data={"data": plain("Hello, world!")},
        ) as (actual, _):
            assert actual == "Hello, world!"


class TestFilterLocalizedUrl(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "data", "absolute"),
        [
            ("/index.html", "/index.html", False),
            ("https://example.com/index.html", "/index.html", True),
        ],
    )
    async def test(self, expected: str, data: Any, absolute: bool) -> None:
        template = "{{ data | localized_url(absolute=absolute) }}"
        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
                "absolute": absolute,
            },
        ) as (actual, _):
            assert actual == expected


class TestFilterNegotiateHasDates(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": None,
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple"),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": None,
                },
            ),
            (
                "",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
                        _DummyHasDate("Apple", Date(1970, 1, 1)),
                    ],
                    "date": Date(1970, 1, 1),
                },
            ),
            (
                "Apple",
                {
                    "has_dates": [
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
        template = '{{ has_dates | negotiate_has_dates(date=date) or "" }}'
        async with self.assert_template_string(template=template, data=data) as (
            actual,
            _,
        ):
            assert actual == expected


class TestFilterNegotiateLocalizeds(TemplateStringTestBase):
    class _Localized(Localized):
        def __init__(self, locale: str):
            self._locale = locale

    async def test(self) -> None:
        localized_en = self._Localized("en")
        localized_nl = self._Localized("nl")
        localizeds = [localized_en, localized_nl]
        template = "{{ (data | negotiate_localizeds).locale }}"
        async with self.assert_template_string(
            template=template, data={"data": localizeds}, locale="nl"
        ) as (actual, _):
            assert actual == "nl"


class TestFilterPublicCss(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ data | public_css }}{{ public_css_paths | safe }}"
        async with self.assert_template_string(
            template=template,
            data={"data": "/css/my-first-css.css"},
        ) as (actual, _):
            assert actual == "None{'/css/my-first-css.css'}"


class TestFilterPublicJs(TemplateStringTestBase):
    async def test(self) -> None:
        template = "{{ data | public_js }}{{ public_js_paths | safe }}"
        async with self.assert_template_string(
            template=template,
            data={"data": "/js/my-first-js.js"},
        ) as (actual, _):
            assert actual == "None{'/js/my-first-js.js'}"


class TestFilterStaticUrl(TemplateStringTestBase):
    @pytest.mark.parametrize(
        ("expected", "data", "absolute"),
        [
            ("/index.html", "/index.html", False),
            ("https://example.com/index.html", "/index.html", True),
        ],
    )
    async def test(self, expected: str, data: Any, absolute: bool) -> None:
        template = "{{ data | static_url(absolute=absolute) }}"
        async with self.assert_template_string(
            template=template,
            data={
                "data": data,
                "absolute": absolute,
            },
        ) as (actual, _):
            assert actual == expected
