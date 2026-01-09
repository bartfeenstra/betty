from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

import pytest

from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import Localizer
from betty.wiki import NotAPageError, parse_page_link, parse_page_url

if TYPE_CHECKING:
    from betty.locale.localizable import StaticTranslationsMapping

_PAGE_URL_PARAMETERS = [
    (
        ("en", "Amsterdam"),
        "http://en.wikipedia.org/wiki/Amsterdam",
    ),
    (
        ("nl", "Amsterdam"),
        "https://nl.wikipedia.org/wiki/Amsterdam",
    ),
    (
        ("en", "Amsterdam"),
        "https://en.wikipedia.org/wiki/Amsterdam/",
    ),
    (
        ("en", "Amsterdam"),
        "https://en.wikipedia.org/wiki/Amsterdam/some-path",
    ),
    (
        ("en", "Amsterdam"),
        "https://en.wikipedia.org/wiki/Amsterdam?some=query",
    ),
    (
        ("en", "Amsterdam"),
        "https://en.wikipedia.org/wiki/Amsterdam#some-fragment",
    ),
]


@pytest.mark.parametrize(
    ("expected", "url"),
    _PAGE_URL_PARAMETERS,
)
async def test_parse_page_url__should_return(
    expected: tuple[str, str], url: str
) -> None:
    assert expected == parse_page_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://en.wikipedia.org/wiki/Amsterdam",
        "https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit",
    ],
)
async def test_parse_page_url__should_error(url: str) -> None:
    with pytest.raises(NotAPageError):
        parse_page_url(url)


@pytest.mark.parametrize(
    ("expected", "url"),
    _PAGE_URL_PARAMETERS,
)
async def test_parse_page_link__should_return(
    expected: tuple[str, str], url: str
) -> None:
    localizers = [
        Localizer("en", NullTranslations()),
        Localizer("nl", NullTranslations()),
    ]
    link = Link(url)
    assert expected == parse_page_link(link, localizers)


@pytest.mark.parametrize(
    "urls",
    [
        {
            DEFAULT_LOCALE_TAG: "",
        },
        {
            DEFAULT_LOCALE_TAG: "ftp://en.wikipedia.org/wiki/Amsterdam",
        },
        {
            DEFAULT_LOCALE_TAG: "https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit",
        },
        {
            DEFAULT_LOCALE_TAG: "https://en.wikipedia.org/wiki/Amsterdam",
            None: "https://und.wikipedia.org/wiki/Amsterdam",
        },
    ],
)
async def test_parse_page_link__should_error(urls: StaticTranslationsMapping) -> None:
    localizers = [
        Localizer("en", NullTranslations()),
        Localizer("nl", NullTranslations()),
    ]
    link = Link(StaticTranslations(urls))
    with pytest.raises(NotAPageError):
        parse_page_link(link, localizers)
