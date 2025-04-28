"""
Fetch content from the internet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.fetch import Fetcher, FetchError, FetchResponse
from betty.locale.localizable import static

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class StaticFetcher(Fetcher):
    """
    Return predefined (static) fetch responses.
    """

    def __init__(
        self,
        *,
        fetch_map: Mapping[str, FetchResponse] | None = None,
        fetch_file_map: Mapping[str, Path] | None = None,
    ):
        self._fetch_map = fetch_map or {}
        self._fetch_file_map = fetch_file_map or {}

    @override
    async def fetch(self, url: str) -> FetchResponse:
        try:
            return self._fetch_map[url]
        except KeyError:
            raise FetchError(static("")) from None

    @override
    async def fetch_file(self, url: str) -> Path:
        try:
            return self._fetch_file_map[url]
        except KeyError:
            raise FetchError(static("")) from None
