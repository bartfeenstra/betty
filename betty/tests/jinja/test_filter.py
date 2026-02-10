from __future__ import annotations

import datetime
from gettext import NullTranslations
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import pytest
from babel import Locale
from PIL import Image
from puremagic import what
from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.content_provider.content_providers import Render, RenderConfiguration
from betty.date import Date, DateRange, ResolvableDate
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.document import Document
from betty.job import Context as JobContext
from betty.locale import HasLocale, HasLocaleStr
from betty.locale.localizable.plain import Plain
from betty.locale.localize import Localizer
from betty.media_type import MediaType
from betty.media_type.media_types import SVG
from betty.plugin.config import PluginConfiguration
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.jinja import assert_template_string
from betty.test_utils.model import DummyEntityOne

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping, Sequence

    from betty.content_provider import ContentProvider, ContentProviderDefinition


class _DummyHasDate(DummyHasDate):
    def __init__(self, value: str, date: ResolvableDate | None = None):
        super().__init__(date=date)
        self.value = value

    @override
    def __str__(self) -> str:
        return self.value


class _DummyHasLocale(HasLocale):
    def __init__(self, value: str, locale: str):
        super().__init__(locale=locale)
        self.value = value


_TEST_FILTER_FILE_PARAMETER_ARGNAMES = ("expected", "template", "file")
_TEST_FILTER_FILE_PARAMETER_ARGVALUES = [
    (
        "betty-static:///file/F1/file/test_filter.py",
        "{{ file | file }}",
        File(
            id="F1",
            path=Path(__file__),
        ),
    ),
    (
        "betty-static:///file/F1/file/test_filter.py#betty-static:///file/F1/file/test_filter.py",
        "{{ file | file }}#{{ file | file }}",
        File(
            id="F1",
            path=Path(__file__),
        ),
    ),
]


@pytest.mark.parametrize(
    _TEST_FILTER_FILE_PARAMETER_ARGNAMES, _TEST_FILTER_FILE_PARAMETER_ARGVALUES
)
async def test_filter_file(expected: str, template: str, file: File) -> None:
    async with assert_template_string(
        template=template,
        data={
            "file": file,
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split("#"):
            assert (project.www_directory / file_path[16:]).exists()


@pytest.mark.parametrize(
    _TEST_FILTER_FILE_PARAMETER_ARGNAMES, _TEST_FILTER_FILE_PARAMETER_ARGVALUES
)
async def test_filter_file__with_job_context(
    expected: str, template: str, file: File
) -> None:
    async with assert_template_string(
        template=template,
        data={
            "file": file,
            "job_context": JobContext(),
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split("#"):
            assert (project.www_directory / file_path[16:]).exists()


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
async def test_filter_flatten(expected: str, template: str) -> None:
    async with assert_template_string(template=template) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "template"),
    [
        ("0° 0&#39; 0&#34;", "{{ 0 | format_degrees }}"),
        ("52° 22&#39; 1&#34;", "{{ 52.367 | format_degrees }}"),
    ],
)
async def test_filter_format_degrees(expected: str, template: str) -> None:
    async with assert_template_string(template=template) as (actual, _):
        assert actual == expected


async def test_filter_unique() -> None:
    data: Sequence[Any] = [
        999,
        {},
        999,
        {},
    ]
    async with assert_template_string(
        template='{{ data | unique | join(", ") }}',
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == "999, {}"


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
async def test_filter_map(expected: str, template: str, data: MapData) -> None:
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH = (
    ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
)
_TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES = ("expected", "template", "filey")
_TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES = [
    (
        "betty-static:///file/F1-99x-.png",
        "{{ filey | image_resize_cover((99, none)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1--x99.png",
        "{{ filey | image_resize_cover((none, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99-1x2x3x4.png",
        "{{ filey | image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png#betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}#{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="F1",
                path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
    ),
    (
        "betty-static:///file/F1-99x99-0x0x9x9.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="F1",
                path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
            focus=(0, 0, 9, 9),
        ),
    ),
]


@pytest.mark.parametrize(
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES,
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES,
)
async def test_filter_image_resize_cover(
    expected: str, template: str, filey: File
) -> None:
    async with assert_template_string(
        template=template,
        data={
            "filey": filey,
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split("#"):
            assert (project.www_directory / file_path[16:]).exists()


@pytest.mark.parametrize(
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES,
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES,
)
async def test_filter_image_resize_cover__with_job_context(
    expected: str, template: str, filey: File
) -> None:
    async with assert_template_string(
        template=template,
        data={
            "filey": filey,
            "job_context": JobContext(),
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split("#"):
            assert (project.www_directory / file_path[16:]).exists()


async def test_filter_image_resize_cover__with_svg(tmp_path: Path) -> None:
    image_path = tmp_path / "image.svg"
    async with aiofiles.open(image_path, "w") as f:
        await f.write(
            '<?xml version="1.0" encoding="UTF-8"?><svg version="1.1" xmlns="http://www.w3.org/2000/svg"></svg>'
        )
    async with assert_template_string(
        template="{{ filey | image_resize_cover }}",
        data={
            "filey": File(
                id="F1",
                path=image_path,
                media_type=SVG,
            )
        },
    ) as (actual, project):
        assert actual == "betty-static:///file/F1/file/image.svg"
        for file_path in actual.split("#"):
            assert (project.www_directory / file_path[16:]).exists()


async def test_filter_image_resize_cover__with_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "image.pdf"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    async with assert_template_string(
        template="{{ filey | image_resize_cover }}",
        data={
            "filey": File(
                id="F1",
                path=image_path,
                media_type=MediaType("application/pdf"),
            )
        },
    ) as (actual, project):
        assert actual == "betty-static:///file/F1-.jpg"
        for public_file_path in actual.split("#"):
            file_path = project.www_directory / public_file_path[16:]
            assert (file_path).exists()
            assert what(file_path) == "jpeg"


async def test_filter_image_resize_cover__with_invalid_image(tmp_path: Path) -> None:
    file_path = tmp_path / "not-an-image.txt"
    file_path.touch()
    with pytest.raises(ValueError):  # noqa: PT011
        async with assert_template_string(
            template="{{ filey | image_resize_cover }}",
            data={
                "filey": File(
                    id="F1",
                    path=file_path,
                    media_type=MediaType("text/plain"),
                )
            },
        ):
            pass  # pragma: nocover


async def test_filter_image_resize_cover__with_file_without_media_type(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        async with assert_template_string(
            template="{{ filey | image_resize_cover }}",
            data={
                "filey": File(id="F1", path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH)
            },
        ):
            pass  # pragma: nocover


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
async def test_filter_select_has_dates(
    expected: str, data: MutableMapping[str, Any]
) -> None:
    template = '{{ has_dates | select_has_dates(date=date) | join(", ") }}'
    async with assert_template_string(template=template, data=data) as (
        actual,
        _,
    ):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "locale", "data"),
    [
        ("", "en", []),
        (
            "en",
            "en",
            [HasLocale(locale="en")],
        ),
        (
            "en_US",
            "en",
            [HasLocale(locale="en-US")],
        ),
        (
            "en",
            "en-US",
            [HasLocale(locale="en")],
        ),
        (
            "",
            "nl",
            [HasLocale(locale="en")],
        ),
        (
            "",
            "nl-NL",
            [HasLocale(locale="en")],
        ),
    ],
)
async def test_filter_select_has_locales(
    expected: str, locale: str, data: Iterable[HasLocale]
) -> None:
    template = '{{ data | select_has_locales | map(attribute="locale") | join(", ") }}'

    async with assert_template_string(
        template=template,
        data={
            "data": data,
            "document": Document(localizer=Localizer(locale, NullTranslations())),
        },
    ) as (actual, _):
        assert actual == expected


async def test_filter_select_has_locales__include_unspecified() -> None:
    template = '{{ data | select_has_locales(include_unspecified=true) | map(attribute="locale") | join(", ") }}'
    data = [HasLocale()]

    async with assert_template_string(
        template=template,
        data={
            "data": data,
            "document": Document(localizer=Localizer("en-US", NullTranslations())),
        },
    ) as (actual, _):
        assert actual == "None"


class WithHasLocales:
    def __init__(self, identifier: str, names: Sequence[HasLocale]):
        self.id = identifier
        self.names = names

    @override
    def __repr__(self) -> str:
        return self.id


async def test_filter_sort_has_locales() -> None:
    template = '{{ data | sort_has_locales(localized_attribute="names", sort_attribute="value") }}'
    data = [
        WithHasLocales(
            "third",
            [
                _DummyHasLocale("3", "nl-NL"),
            ],
        ),
        WithHasLocales(
            "second",
            [
                _DummyHasLocale("2", "en"),
                _DummyHasLocale("1", "nl-NL"),
            ],
        ),
        WithHasLocales(
            "first",
            [
                _DummyHasLocale("2", "nl-NL"),
                _DummyHasLocale("1", "en-US"),
            ],
        ),
    ]
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == "[first, second, third]"


async def test_filter_sort_has_locales__with_empty_iterable() -> None:
    template = '{{ data | sort_has_locales(localized_attribute="names", sort_attribute="value") }}'
    async with assert_template_string(
        template=template,
        data={
            "data": [],
        },
    ) as (actual, _):
        assert actual == "[]"


@pytest.mark.parametrize(
    ("expected", "autoescape", "has_locale", "localizer_locale"),
    [
        ("Hallo, wereld!", True, "Hallo, wereld!", "nl"),
        ("Hallo, wereld!", True, "Hallo, wereld!", "ar"),
        (
            "Hallo, wereld!",
            True,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "nl",
        ),
        (
            "Hallo, wereld!",
            False,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "nl",
        ),
        (
            '<span lang="nl">Hallo, wereld!</span>',
            True,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "en",
        ),
        (
            '<span lang="nl">Hallo, wereld!</span>',
            False,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "en",
        ),
        (
            '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
            True,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "ar",
        ),
        (
            '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
            False,
            HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
            "ar",
        ),
    ],
)
async def test_filter_html_lang(
    expected: str,
    autoescape: bool,
    has_locale: str,
    localizer_locale: str,
) -> None:
    template = "{{ has_locale | html_lang }}"
    async with assert_template_string(
        template=template,
        data={
            "has_locale": has_locale,
            "document": Document(
                localizer=Localizer(localizer_locale, NullTranslations())
            ),
        },
        autoescape=autoescape,
    ) as (actual, _):
        assert actual == expected


async def test_filter_hashid() -> None:
    template = "{{ data | hashid }}"
    async with assert_template_string(
        template=template,
        data={"data": "Hello, world!"},
    ) as (actual, _):
        assert actual == "6cd3556deb0da54bca060b4c39479839"


async def test_filter_json_dump() -> None:
    template = "{{ data | json_dump }}"
    async with assert_template_string(
        template=template,
        data={"data": [1, 2, 3]},
    ) as (actual, _):
        assert actual == "[1, 2, 3]"


async def test_filter_json_load() -> None:
    data = "[1, 2, 3]"
    template = "{{ data | json_load | json_dump }}"
    async with assert_template_string(
        template=template,
        data={"data": data},
    ) as (actual, _):
        assert actual == data


async def test_filter_localize() -> None:
    template = "{{ data | localize }}"
    async with assert_template_string(
        template=template,
        data={"data": Plain("Hello, world!")},
    ) as (actual, _):
        assert actual == "Hello, world!"


@pytest.mark.parametrize(
    ("expected", "data", "absolute"),
    [
        ("/index.html", "betty:///index.html", False),
        ("/index.html", "betty-static:///index.html", False),
        (
            "https://example.com/dummy-one/0e51a87ec173dd9534a056a403c85881/index.html",
            DummyEntityOne("E0"),
            True,
        ),
    ],
)
async def test_filter_url(expected: str, data: Any, absolute: bool) -> None:
    template = "{{ data | url(absolute=absolute) }}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
            "absolute": absolute,
        },
    ) as (actual, _):
        assert actual == expected


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
async def test_filter_negotiate_has_dates(
    expected: str, data: MutableMapping[str, Any]
) -> None:
    template = '{{ has_dates | negotiate_has_dates(date=date) or "" }}'
    async with assert_template_string(template=template, data=data) as (
        actual,
        _,
    ):
        assert actual == expected


async def test_filter_negotiate_has_locales() -> None:
    has_locale_en = HasLocale(locale=Locale("en"))
    has_locale_nl = HasLocale(locale=Locale("nl"))
    has_locales = [has_locale_en, has_locale_nl]
    template = "{{ (data | negotiate_has_locales).locale }}"
    async with assert_template_string(
        template=template,
        data={
            "data": has_locales,
            "document": Document(localizer=Localizer("nl", NullTranslations())),
        },
    ) as (actual, _):
        assert actual == "nl"


@pytest.mark.parametrize(
    ("expected", "content_provider_configurations"),
    [
        ("", []),
        (
            "<p>Hello, world!</p>",
            [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))],
        ),
    ],
)
async def test_filter_provide_content(
    expected: str,
    content_provider_configurations: Iterable[
        PluginConfiguration[ContentProviderDefinition, ContentProvider]
    ],
) -> None:
    template = "{{ data | provide_content }}"
    async with assert_template_string(
        template=template,
        data={
            "data": content_provider_configurations,
        },
    ) as (actual, _):
        assert actual == expected


async def test_filter_format_datetime_datetime() -> None:
    template = "{{ data | format_datetime_datetime }}"
    async with assert_template_string(
        template=template,
        data={
            "data": datetime.datetime(1970, 1, 1),
        },
    ) as (actual, _):
        assert actual == "January 1, 1970"
