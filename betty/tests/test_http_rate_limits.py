import pytest
from aiohttp import ClientRequest
from yarl import URL

from betty.http_rate_limits import wikipedia_action_api, wikipedia_rest_api


class TestWikipediaActionApi:
    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            (True, "https://en.wikipedia.org/w/api.php"),
            (True, "https://nl.wikipedia.org/w/api.php"),
            (
                True,
                "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2",
            ),
            (True, "http://en.wikipedia.org/w/api.php"),
            (False, "ftp://en.wikipedia.org/w/api.php"),
            (False, "https://en.wikipedia.org/w/api"),
            (False, "https://example.com"),
            (False, "hhttps://en.wikipedia.org/w/api.php"),
        ],
    )
    async def test_match(self, expected: bool, url: str) -> None:
        request = ClientRequest("GET", URL(url))
        assert wikipedia_action_api.match(request) is expected

    def test_limit(self) -> None:
        assert wikipedia_action_api.limit[0]
        assert wikipedia_action_api.limit[1]


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
        assert wikipedia_rest_api.match(request) is expected

    def test_limit(self) -> None:
        assert wikipedia_rest_api.limit[0]
        assert wikipedia_rest_api.limit[1]
