import pytest
from aiohttp import ClientRequest
from yarl import URL

from betty.plugins.rate_limit.wikipedia_rest_api import WIKIPEDIA_REST_API


class TestWikipediaRestApi:
    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            (True, "https://en.wikipedia.org/api/rest_v1"),
            (True, "https://en.wikipedia.org/api/rest_v1/"),
            (True, "https://nl.wikipedia.org/api/rest_v1"),
            (True, "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam"),
            (True, "http://en.wikipedia.org/api/rest_v1"),
            (False, "ftp://en.wikipedia.org/api/rest_v1"),
            (False, "https://en.wikipedia.org/api"),
            (False, "https://example.com"),
        ],
    )
    async def test_match(self, expected: bool, url: str) -> None:
        request = ClientRequest("GET", URL(url))
        assert WIKIPEDIA_REST_API.match(request) is expected

    def test_limit(self) -> None:
        assert WIKIPEDIA_REST_API.limit[0]
        assert WIKIPEDIA_REST_API.limit[1]
