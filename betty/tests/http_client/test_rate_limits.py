import pytest
from aiohttp.client_reqrep import ClientRequest
from typing_extensions import override
from yarl import URL

from betty.http_client.rate_limit import RateLimit
from betty.http_client.rate_limits import WikipediaActionApi, WikipediaRestApi
from betty.plugin import PluginDefinition
from betty.test_utils.http_client.rate_limit import (
    RateLimitDefinitionTestBase,
    RateLimitTestBase,
)


class TestWikipediaActionApiDefinition(RateLimitDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return WikipediaActionApi.plugin()


class TestWikipediaActionApi(RateLimitTestBase):
    @override
    @pytest.fixture
    def sut(self) -> RateLimit:
        return WikipediaActionApi()

    @pytest.mark.parametrize(
        ("expected", "method", "url"),
        [
            (True, "GET", "https://en.wikipedia.org/w/api.php"),
            (True, "GET", "https://nl.wikipedia.org/w/api.php"),
            (
                True,
                "GET",
                "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2",
            ),
            (True, "GET", "http://en.wikipedia.org/w/api.php"),
            (False, "GET", "ftp://en.wikipedia.org/w/api.php"),
            (False, "GET", "https://en.wikipedia.org/w/api"),
            (False, "GET", "https://example.com"),
        ],
    )
    async def test_match(self, expected: bool, method: str, url: str) -> None:
        sut = WikipediaActionApi()
        request = ClientRequest(method, URL(url))
        assert sut.match(request) is expected

    def test_limit(self) -> None:
        sut = WikipediaActionApi()
        assert sut.limit[0]
        assert sut.limit[1]


class TestWikipediaRestApiDefinition(RateLimitDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return WikipediaRestApi.plugin()


class TestWikipediaRestApi(RateLimitTestBase):
    @override
    @pytest.fixture
    def sut(self) -> RateLimit:
        return WikipediaRestApi()

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
