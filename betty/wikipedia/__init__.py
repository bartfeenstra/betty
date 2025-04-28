"""
Fetch information from Wikipedia.
"""

from __future__ import annotations

import re
from typing import cast


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
