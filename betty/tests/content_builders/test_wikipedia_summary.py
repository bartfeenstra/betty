from pytest_mock import MockerFixture

from betty.content_builders.wikipedia_summary import WikipediaSummary
from betty.document import Document
from betty.entities.link import Link
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.entity.associations.has_links import DummyHasLinks
from betty.wiki.client import Summary


class TestWikipediaSummary:
    async def test_build_template__without_has_links_resource(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            supported_plugins=[WikipediaSummary]
        ) as project:
            sut = await WikipediaSummary.new(project)
            assert await sut.build(document=Document()) is None

    async def test_build_template__with_has_links_resource(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        url = "https://en.wikipedia.org/wiki/Amsterdam"
        summary_content = "My first summary content"
        m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
        m_get_summary.return_value = Summary(
            "en", "Amsterdam", "My First Summary", summary_content
        )
        resource = DummyHasLinks(links=[Link(url)])
        async with isolated_project_factory(
            supported_plugins=[WikipediaSummary]
        ) as project:
            project.ancestry.add(resource)
            sut = await WikipediaSummary.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert url in actual
        assert summary_content in actual
