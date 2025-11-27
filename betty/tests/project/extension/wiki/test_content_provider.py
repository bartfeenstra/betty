from pytest_mock import MockerFixture

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.app import App
from betty.locale.localizable import CountablePlain
from betty.model import EntityPlugin
from betty.project import Project
from betty.project.extension.wiki import Wiki
from betty.project.extension.wiki.content_provider import WikipediaSummary
from betty.resource import new_context
from betty.wiki.client import Summary


@EntityPlugin(
    "dummy-has-links",
    label="",
    label_plural="",
    label_countable=CountablePlain("", ""),
)
class DummyHasLinks(HasLinks):
    pass


class TestWikipediaSummary:
    async def test_provide__without_has_links_resource(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                sut = await WikipediaSummary.new_for_project(project)
                assert await sut.provide(resource=new_context()) is None

    async def test_provide__with_has_links_resource(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        url = "https://en.wikipedia.org/wiki/Amsterdam"
        summary_content = "My first summary content"
        m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
        m_get_summary.return_value = Summary(
            "en", "Amsterdam", "My First Summary", summary_content
        )
        resource = DummyHasLinks(links=[Link(url)])
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                project.ancestry.add(resource)
                sut = await WikipediaSummary.new_for_project(project)
                actual = await sut.provide(resource=new_context(resource))
        assert actual is not None
        assert url in actual
        assert summary_content in actual
