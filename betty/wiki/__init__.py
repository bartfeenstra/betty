"""
Fetch information from Wikipedia.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from betty.locale.localizable import StaticTranslations

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.link import Link
    from betty.locale.localizer import Localizer


class NotAPageError(ValueError):
    """
    Raised when a URL does not point to a Wikipedia page.
    """


_PAGE_URL_PATTERN = re.compile(r"^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$")


def parse_page_url(url: str) -> tuple[str, str]:
    """
    Parse the URL for a Wikipedia page.

    :return: A 2-tuple with the page language and the page name.
    """
    match = _PAGE_URL_PATTERN.fullmatch(url)
    if match is None:
        raise NotAPageError
    return cast(tuple[str, str], match.groups())


def parse_page_link(link: Link, localizers: Sequence[Localizer]) -> tuple[str, str]:
    """
    Parse the URL for a link to a Wikipedia page.

    :return: A 2-tuple with the page language and the page name.
    """
    original_urls = set(
        StaticTranslations.from_localizable(link.url, localizers).translations.values()
    )
    if len(original_urls) > 1:
        # Skip links that already provide different localized URLs, as things would get too complex.
        raise NotAPageError
    original_url = next(iter(original_urls))
    return parse_page_url(original_url)
