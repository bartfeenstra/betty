from json import dumps
from typing import Any

import pytest
from multidict import CIMultiDict
from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.fetch import FetchResponse
from betty.fetch.static import StaticFetcher
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition
from betty.test_utils.conftest import NewTemporaryAppFactory
from betty.test_utils.copyright_notice import (
    CopyrightNoticeDefinitionTestBase,
    CopyrightNoticeTestBase,
)
from betty.wiki.copyright_notice import WikipediaContributors


def _new_json_fetch_response(json_data: Any) -> FetchResponse:
    return FetchResponse(CIMultiDict(), dumps(json_data).encode("utf-8"), "utf-8")


class TestWikipediaContributorsDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return WikipediaContributors.plugin


class TestWikipediaContributors(CopyrightNoticeTestBase):
    @override
    @pytest.fixture(
        params=[
            {},
            {"en": "Wikipedia:Copyrights"},
            {"en": "Wikipedia:Copyrights", "nl": "Wikipedia:Auteursrechten"},
        ]
    )
    def sut(self, request: pytest.FixtureRequest) -> CopyrightNotice:
        return WikipediaContributors(request.param)

    async def test_new_for_app(
        self, new_temporary_app_factory: NewTemporaryAppFactory
    ) -> None:
        response_json = {
            "continue": {"llcontinue": "49479|an", "continue": "||"},
            "query": {
                "pages": [
                    {
                        "pageid": 49479,
                        "ns": 4,
                        "title": "Wikipedia:Copyrights",
                        "langlinks": [
                            {"lang": "ab", "title": "Авикипедиа:Автортə зинқәа"},
                            {"lang": "af", "title": "Wikipedia:Kopiereg"},
                            {
                                "lang": "als",
                                "title": "Wikipedia:Urheberrechte beachten",
                            },
                        ],
                    }
                ]
            },
        }
        fetcher = StaticFetcher(
            fetch_map={
                "https://en.wikipedia.org/w/api.php?action=query&titles=Wikipedia:Copyrights&prop=langlinks&lllimit=500&format=json&formatversion=2": _new_json_fetch_response(
                    response_json
                )
            }
        )
        async with (
            new_temporary_app_factory(fetcher=fetcher) as app,
            app,
        ):
            sut = await WikipediaContributors.new_for_app(app)
            assert sut.url.localize(DEFAULT_LOCALIZER)
