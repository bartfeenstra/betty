from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING, Final

import pytest

from betty.entities.link import Link
from betty.locale import default_locale_tag
from betty.localizables.static import StaticTranslations
from betty.localizer import Localizer
from betty.wiki import NotAPageError, parse_page_link, parse_page_url

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizables.static import StaticTranslationsMapping

_page_url_parameters: Final[Sequence[tuple[tuple[str, str], str]]] = [
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
    _page_url_parameters,
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
    _page_url_parameters,
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
            default_locale_tag: "",
        },
        {
            default_locale_tag: "ftp://en.wikipedia.org/wiki/Amsterdam",
        },
        {
            default_locale_tag: "https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit",
        },
        {
            default_locale_tag: "https://en.wikipedia.org/wiki/Amsterdam",
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
