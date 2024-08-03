from unittest.mock import PropertyMock


from betty.extension.wikipedia import Wikipedia
from betty.ancestry import HasLinks, Link
from betty.test_utils.assets.templates import TemplateTestBase
from pytest_mock import MockerFixture

from betty.test_utils.model import DummyEntity
from betty.wikipedia import _Retriever, Summary


class DummyResource(HasLinks, DummyEntity):
    pass


class Test(TemplateTestBase):
    extensions = {Wikipedia}
    template_file = "wikipedia.html.j2"

    async def test_without_links(self) -> None:
        resource = DummyResource()
        async with self._render(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_links_without_wikipedia_links(self) -> None:
        resource = DummyResource()
        resource.links.append(Link("https://example.com"))
        async with self._render(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_without_summaries(self, mocker: MockerFixture) -> None:
        wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
        m_retriever = mocker.AsyncMock(spec=_Retriever)
        m_retriever.get_summary.return_value = None
        mocker.patch(
            "betty.extension.wikipedia.Wikipedia.retriever",
            new_callable=PropertyMock,
            return_value=m_retriever,
        )
        resource = DummyResource()
        resource.links.append(Link(wikipedia_url))
        async with self._render(
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
        async with self._render(
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
        mocker.patch(
            "betty.extension.wikipedia.Wikipedia.retriever",
            new_callable=PropertyMock,
            return_value=m_retriever,
        )
        resource = DummyResource()
        resource.links.append(Link(wikipedia_url))
        async with self._render(
            data={
                "resource": resource,
            }
        ) as (actual, _):
            assert summary.content in actual
        m_retriever.get_summary.assert_called_once_with("en", "Amsterdam")
