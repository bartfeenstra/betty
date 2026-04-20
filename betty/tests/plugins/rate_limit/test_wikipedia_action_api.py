import pytest
from aiohttp import ClientRequest
from yarl import URL

from betty.plugins.rate_limit.wikipedia_action_api import WIKIPEDIA_ACTION_API


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
        assert WIKIPEDIA_ACTION_API.match(request) is expected

    def test_limit(self) -> None:
        assert WIKIPEDIA_ACTION_API.limit[0]
        assert WIKIPEDIA_ACTION_API.limit[1]
