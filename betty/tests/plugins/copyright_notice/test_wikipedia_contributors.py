from json import dumps
from typing import override

import pytest
from aioresponses import aioresponses

from betty.app import App
from betty.copyright_notice import CopyrightNotice
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.copyright_notice.wikipedia_contributors import WikipediaContributors
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestWikipediaContributors(CopyrightNoticeTestBase):
    @override
    @pytest.fixture(
        params=[
            "https://example/com/en",
            StaticTranslations({"en": "https://example/com/en"}),
            StaticTranslations(
                {"en": "https://example/com/en", "nl": "https://example/com/en"}
            ),
        ]
    )
    def sut(self, request: pytest.FixtureRequest) -> CopyrightNotice:
        return WikipediaContributors(request.param)

    async def test_new(self, http_client_mock: aioresponses, isolated_app: App) -> None:
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
        http_client_mock.get(
            "https://en.wikipedia.org/w/api.php?action=query&titles=Wikipedia:Copyrights&prop=langlinks&lllimit=500&format=json&formatversion=2",
            body=dumps(response_json),
        )
        sut = await WikipediaContributors.new(isolated_app)
        assert sut.url.localize(DEFAULT_LOCALIZER)
