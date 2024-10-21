from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from betty.ancestry.link import HasLinks, Link
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.wikipedia import Wikipedia
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.test_utils.model import DummyEntity
from betty.wikipedia import _Retriever, Summary
from betty.wikipedia.copyright_notice import WikipediaContributors


class DummyResource(HasLinks, DummyEntity):
    pass


class Test(TemplateFileTestBase):
    extensions = {Wikipedia}
    template = "wikipedia.html.j2"

    async def test_without_links(self) -> None:
        resource = DummyResource()
        async with self.assert_template_file(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_links_without_wikipedia_links(self) -> None:
        resource = DummyResource()
        resource.links.append(Link("https://example.com"))
        async with self.assert_template_file(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_without_summaries(self, mocker: MockerFixture) -> None:
        wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
        m_retriever = mocker.AsyncMock(spec=_Retriever)
        m_retriever.get_summary.return_value = None

        async def _awaitable_retriever():
            return m_retriever  # type: ignore[no-any-return]

        mocker.patch(
            "betty.project.extension.wikipedia.Wikipedia.retriever",
            new_callable=PropertyMock,
            return_value=_awaitable_retriever(),
        )
        resource = DummyResource()
        resource.links.append(Link(wikipedia_url))
        async with self.assert_template_file(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""
        m_retriever.get_summary.assert_called_once_with("en", "Amsterdam")

    async def test_with_summaries_in_irrelevant_locale(self) -> None:
        wikipedia_url = "https://nl.wikipedia.org/wiki/Amsterdam"
        resource = DummyResource()
        resource.links.append(Link(wikipedia_url))
        async with self.assert_template_file(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_summary_should_render(self, mocker: MockerFixture) -> None:
        wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
        summary = Summary(
            "en", "Amsterdam", "Amstelredam", "Capital of the Netherlands"
        )
        m_retriever = mocker.AsyncMock(spec=_Retriever)
        m_retriever.get_summary.return_value = summary

        async def _awaitable_retriever():
            return m_retriever  # type: ignore[no-any-return]

        mocker.patch(
            "betty.project.extension.wikipedia.Wikipedia.retriever",
            new_callable=PropertyMock,
            return_value=_awaitable_retriever(),
        )
        resource = DummyResource()
        resource.links.append(Link(wikipedia_url))
        async with self.assert_template_file(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert summary.content in actual
            wikipedia_contributors_copyright_notice = WikipediaContributors({})
            assert (
                wikipedia_contributors_copyright_notice.summary.localize(
                    DEFAULT_LOCALIZER
                )
                in actual
            )
            assert (
                wikipedia_contributors_copyright_notice.url.localize(DEFAULT_LOCALIZER)
                in actual
            )
        m_retriever.get_summary.assert_called_once_with("en", "Amsterdam")
