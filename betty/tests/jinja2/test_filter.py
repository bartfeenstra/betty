from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import pytest
from PIL import Image
from puremagic import what

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.date import Date, DateRange, Datey
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.job import Context
from betty.locale import (
    MULTIPLE_LOCALES,
    NO_LINGUISTIC_CONTENT,
    UNCODED_LOCALE,
    UNDETERMINED_LOCALE,
)
from betty.locale.localizable import plain
from betty.locale.localized import Localized, LocalizedStr
from betty.media_type import MediaType
from betty.media_type.media_types import SVG
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.jinja2 import assert_template_string
from betty.test_utils.locale.localized import DummyLocalized
from betty.test_utils.model import DummyEntity
from betty.tests.ancestry.test___init__ import DummyHasFileReferences
from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping, Sequence
    from multiprocessing.managers import SyncManager


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


_TEST_FILTER_FILE_PARAMETER_ARGNAMES = ("expected", "template", "file")
_TEST_FILTER_FILE_PARAMETER_ARGVALUES = [
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
        for file_path in actual.split(":"):
            assert (project.configuration.www_directory_path / file_path[1:]).exists()


@pytest.mark.parametrize(
    _TEST_FILTER_FILE_PARAMETER_ARGNAMES, _TEST_FILTER_FILE_PARAMETER_ARGVALUES
)
async def test_filter_file__with_job_context(
    expected: str,
    template: str,
    file: File,
    multiprocessing_manager: SyncManager,
) -> None:
    async with assert_template_string(
        template=template,
        data={
            "file": file,
            "job_context": Context(manager=multiprocessing_manager),
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split(":"):
            assert (project.configuration.www_directory_path / file_path[1:]).exists()


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
async def test_filter_paragraphs(
    expected: str, autoescape: bool, template: str
) -> None:
    async with assert_template_string(template=template, autoescape=autoescape) as (
        actual,
        _,
    ):
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
        "/file/F1-99x-.png",
        "{{ filey | image_resize_cover((99, none)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "/file/F1--x99.png",
        "{{ filey | image_resize_cover((none, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "/file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "/file/F1-99x99-1x2x3x4.png",
        "{{ filey | image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "/file/F1-99x99.png:/file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}:{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "/file/F1-99x99.png",
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
        "/file/F1-99x99-0x0x9x9.png",
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
        for file_path in actual.split(":"):
            assert (project.configuration.www_directory_path / file_path[1:]).exists()


@pytest.mark.parametrize(
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES,
    _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES,
)
async def test_filter_image_resize_cover__with_job_context(
    expected: str,
    template: str,
    filey: File,
    multiprocessing_manager: SyncManager,
) -> None:
    async with assert_template_string(
        template=template,
        data={
            "filey": filey,
            "job_context": Context(manager=multiprocessing_manager),
        },
    ) as (actual, project):
        assert actual == expected
        for file_path in actual.split(":"):
            assert (project.configuration.www_directory_path / file_path[1:]).exists()


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
        assert actual == "/file/F1/file/image.svg"
        for file_path in actual.split(":"):
            assert (project.configuration.www_directory_path / file_path[1:]).exists()


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
        assert actual == "/file/F1-.jpg"
        for public_file_path in actual.split(":"):
            file_path = project.configuration.www_directory_path / public_file_path[1:]
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
async def test_filter_select_localizeds(
    expected: str, locale: str, data: Iterable[Localized]
) -> None:
    template = '{{ data | select_localizeds | map(attribute="locale") | join(", ") }}'

    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
        locale=locale,
    ) as (actual, _):
        assert actual == expected


async def test_filter_select_localizeds__include_unspecified() -> None:
    template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="locale") | join(", ") }}'
    data = [
        DummyLocalized(locale=NO_LINGUISTIC_CONTENT),
        DummyLocalized(locale=UNDETERMINED_LOCALE),
        DummyLocalized(locale=MULTIPLE_LOCALES),
        DummyLocalized(locale=UNCODED_LOCALE),
    ]

    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
        locale="en-US",
    ) as (actual, _):
        assert actual == "zxx, und, mul, mis"


class WithLocalizedDummyLocalizeds:
    def __init__(self, identifier: str, names: Sequence[DummyLocalized]):
        self.id = identifier
        self.names = names

    def __repr__(self) -> str:
        return self.id


async def test_filter_sort_localizeds() -> None:
    template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="value") }}'
    data = [
        WithLocalizedDummyLocalizeds(
            "third",
            [
                _DummyLocalized("3", "nl-NL"),
            ],
        ),
        WithLocalizedDummyLocalizeds(
            "second",
            [
                _DummyLocalized("2", "en"),
                _DummyLocalized("1", "nl-NL"),
            ],
        ),
        WithLocalizedDummyLocalizeds(
            "first",
            [
                _DummyLocalized("2", "nl-NL"),
                _DummyLocalized("1", "en-US"),
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


async def test_filter_sort_localizeds__with_empty_iterable() -> None:
    template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="value") }}'
    async with assert_template_string(
        template=template,
        data={
            "data": [],
        },
    ) as (actual, _):
        assert actual == "[]"


async def test_filter_format_datey() -> None:
    template = "{{ date | format_datey }}"
    date = Date(1970, 1, 1)
    async with assert_template_string(
        template=template,
        data={
            "date": date,
        },
    ) as (actual, _):
        assert actual == "January 1, 1970"


@pytest.mark.parametrize(
    ("expected", "autoescape", "localized", "localizer_locale"),
    [
        ("Hallo, wereld!", True, "Hallo, wereld!", "nl"),
        ("Hallo, wereld!", True, "Hallo, wereld!", "ar"),
        ("Hallo, wereld!", True, LocalizedStr("Hallo, wereld!", locale="nl"), "nl"),
        (
            "Hallo, wereld!",
            False,
            LocalizedStr("Hallo, wereld!", locale="nl"),
            "nl",
        ),
        (
            '<span lang="nl">Hallo, wereld!</span>',
            True,
            LocalizedStr("Hallo, wereld!", locale="nl"),
            "en",
        ),
        (
            '<span lang="nl">Hallo, wereld!</span>',
            False,
            LocalizedStr("Hallo, wereld!", locale="nl"),
            "en",
        ),
        (
            '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
            True,
            LocalizedStr("Hallo, wereld!", locale="nl"),
            "ar",
        ),
        (
            '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
            False,
            LocalizedStr("Hallo, wereld!", locale="nl"),
            "ar",
        ),
    ],
)
async def test_filter_html_lang(
    expected: str,
    autoescape: bool,
    localized: LocalizedStr | str,
    localizer_locale: str,
) -> None:
    template = "{{ localized | html_lang }}"
    async with assert_template_string(
        template=template,
        data={
            "localized": localized,
        },
        autoescape=autoescape,
        locale=localizer_locale,
    ) as (actual, _):
        assert actual == expected


async def test_filter_hashid() -> None:
    template = "{{ data | hashid }}"
    async with assert_template_string(
        template=template,
        data={"data": "Hello, world!"},
    ) as (actual, _):
        assert actual == "6cd3556deb0da54bca060b4c39479839"


async def test_filter_json() -> None:
    template = "{{ data | json }}"
    async with assert_template_string(
        template=template,
        data={"data": [1, 2, 3]},
    ) as (actual, _):
        assert actual == "[1, 2, 3]"


async def test_filter_localize() -> None:
    template = "{{ data | localize }}"
    async with assert_template_string(
        template=template,
        data={"data": plain("Hello, world!")},
    ) as (actual, _):
        assert actual == "Hello, world!"


@pytest.mark.parametrize(
    ("expected", "data", "absolute"),
    [
        ("/index.html", "betty:///index.html", False),
        ("/index.html", "betty-static:///index.html", False),
        ("https://example.com/dummy-entity/E0/index.html", DummyEntity("E0"), True),
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
    ("expected", "data", "absolute"),
    [
        ("/index.html", "/index.html", False),
        ("https://example.com/index.html", "/index.html", True),
    ],
)
async def test_filter_localized_url(expected: str, data: Any, absolute: bool) -> None:
    template = "{{ data | localized_url(absolute=absolute) }}"
    with pytest.warns(BettyDeprecationWarning):
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


class _Localized(Localized):
    def __init__(self, locale: str):
        self._locale = locale


async def test_filter_negotiate_localizeds() -> None:
    localized_en = _Localized("en")
    localized_nl = _Localized("nl")
    localizeds = [localized_en, localized_nl]
    template = "{{ (data | negotiate_localizeds).locale }}"
    async with assert_template_string(
        template=template, data={"data": localizeds}, locale="nl"
    ) as (actual, _):
        assert actual == "nl"


async def test_filter_public_css() -> None:
    template = "{{ data | public_css }}{{ public_css_paths | safe }}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={"data": "betty-static:///css/my-first-css.css"},
        ) as (actual, _):
            assert actual == "None['/css/my-first-css.css']"


async def test_filter_public_css__with_deprecated_url_path() -> None:
    template = "{{ data | public_css }}{{ public_css_paths | safe }}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={"data": "/css/my-first-css.css"},
        ) as (actual, _):
            assert actual == "None['/css/my-first-css.css']"


async def test_filter_public_js() -> None:
    template = "{{ data | public_js }}{{ public_js_paths | safe }}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={"data": "betty-static:///js/my-first-js.js"},
        ) as (actual, _):
            assert actual == "None['/js/my-first-js.js']"


async def test_filter_public_js__with_deprecated_url_path() -> None:
    template = "{{ data | public_js }}{{ public_js_paths | safe }}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={"data": "/js/my-first-js.js"},
        ) as (actual, _):
            assert actual == "None['/js/my-first-js.js']"


@pytest.mark.parametrize(
    ("expected", "data", "absolute"),
    [
        ("/index.html", "/index.html", False),
        ("https://example.com/index.html", "/index.html", True),
    ],
)
async def test_filter_static_url(expected: str, data: Any, absolute: bool) -> None:
    template = "{{ data | static_url(absolute=absolute) }}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={
                "data": data,
                "absolute": absolute,
            },
        ) as (actual, _):
            assert actual == expected
