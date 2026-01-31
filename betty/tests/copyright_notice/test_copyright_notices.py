from json import dumps

import pytest
from aioresponses import aioresponses
from typing_extensions import override

from betty.app import App
from betty.copyright_notice import CopyrightNotice
from betty.copyright_notice.copyright_notices import (
    ProjectAuthor,
    PublicDomain,
    Streetmix,
    WikipediaContributors,
)
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition
from betty.test_utils.copyright_notice import (
    CopyrightNoticeDefinitionTestBase,
    CopyrightNoticeTestBase,
)


class TestProjectAuthorDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return ProjectAuthor.plugin()


class TestProjectAuthor(CopyrightNoticeTestBase):
    @override
    @pytest.fixture(
        params=[
            None,
            "My First Author",
        ]
    )
    def sut(self, request: pytest.FixtureRequest) -> CopyrightNotice:
        return ProjectAuthor(request.param)


class TestPublicDomainDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return PublicDomain.plugin()


class TestPublicDomain(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return PublicDomain()


class TestStreetmixDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Streetmix.plugin()


class TestStreetmix(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return Streetmix()


class TestWikipediaContributorsDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return WikipediaContributors.plugin()


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

    async def test_new_for_services(
        self, http_client_mock: aioresponses, isolated_app: App
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
        http_client_mock.get(
            "https://en.wikipedia.org/w/api.php?action=query&titles=Wikipedia:Copyrights&prop=langlinks&lllimit=500&format=json&formatversion=2",
            body=dumps(response_json),
        )
        sut = await WikipediaContributors.new_for_services(services=isolated_app)
        assert sut.url.localize(DEFAULT_LOCALIZER)
