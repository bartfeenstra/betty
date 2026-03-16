import pytest
from aiohttp import ClientRequest
from yarl import URL

from betty.plugins.rate_limit.wikipedia_rest_api import WikipediaRestApi


class TestWikipediaRestApi:
    @pytest.mark.parametrize(
        ("expected", "method", "url"),
        [
            (True, "GET", "https://en.wikipedia.org/api/rest_v1"),
            (True, "GET", "https://nl.wikipedia.org/api/rest_v1"),
            (
                True,
                "GET",
                "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam",
            ),
            (True, "GET", "http://en.wikipedia.org/api/rest_v1"),
            (False, "GET", "ftp://en.wikipedia.org/api/rest_v1"),
            (False, "GET", "https://en.wikipedia.org/api"),
            (False, "GET", "https://example.com"),
        ],
    )
    async def test_match(self, expected: bool, method: str, url: str) -> None:
        sut = WikipediaRestApi()
        request = ClientRequest(method, URL(url))
        assert sut.match(request) is expected

    def test_limit(self) -> None:
        sut = WikipediaRestApi()
        assert sut.limit[0]
        assert sut.limit[1]
