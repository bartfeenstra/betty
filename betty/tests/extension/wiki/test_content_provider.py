import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.ancestry.link import Link
from betty.app import App
from betty.content_provider import ContentProvider
from betty.document import Document
from betty.extension.wiki import Wiki
from betty.extension.wiki.content_provider import WikipediaSummary
from betty.project import Project
from betty.test_utils.ancestry.has_links import DummyHasLinks
from betty.test_utils.content_provider import ContentProviderTestBase
from betty.wiki.client import Summary


class TestWikipediaSummary(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return WikipediaSummary(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_has_links_resource(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                sut = await WikipediaSummary.new_for_services(project)
                assert await sut.provide(document=Document()) is None

    async def test_provide__with_has_links_resource(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        url = "https://en.wikipedia.org/wiki/Amsterdam"
        summary_content = "My first summary content"
        m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
        m_get_summary.return_value = Summary(
            "en", "Amsterdam", "My First Summary", summary_content
        )
        resource = DummyHasLinks(links=[Link(url)])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                project.ancestry.add(resource)
                sut = await WikipediaSummary.new_for_services(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert url in actual
        assert summary_content in actual
