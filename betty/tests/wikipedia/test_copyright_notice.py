from collections.abc import Sequence

from typing_extensions import override

from betty.app import App
from betty.copyright_notice import CopyrightNotice
from betty.fetch.static import StaticFetcher
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase
from betty.tests.wikipedia.test___init__ import _new_json_fetch_response
from betty.wikipedia.copyright_notice import WikipediaContributors


class TestWikipediaContributors(CopyrightNoticeTestBase):
    @override
    def get_sut_class(self) -> type[CopyrightNotice]:
        return WikipediaContributors

    @override
    def get_sut_instances(self) -> Sequence[CopyrightNotice]:
        return [
            WikipediaContributors({}),
            WikipediaContributors({"en": "Wikipedia:Copyrights"}),
            WikipediaContributors(
                {"en": "Wikipedia:Copyrights", "nl": "Wikipedia:Auteursrechten"}
            ),
        ]

    async def test_new_for_app(self) -> None:
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
        async with App.new_temporary(fetcher=fetcher) as app, app:
            sut = await WikipediaContributors.new_for_app(app)
            assert sut.url.localize(DEFAULT_LOCALIZER)
