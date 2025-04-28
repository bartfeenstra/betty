from __future__ import annotations

import pytest

from betty.wikipedia import NotAPageError, parse_page_url


@pytest.mark.parametrize(
    ("expected", "url"),
    [
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
    ],
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
