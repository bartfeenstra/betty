from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from betty.ancestry.link import HasLinks, Link
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.wikipedia import Wikipedia
from betty.test_utils.jinja2 import assert_template_file
from betty.test_utils.model import DummyEntity
from betty.wikipedia import Summary, _Retriever
from betty.wikipedia.copyright_notice import WikipediaContributors


class DummyResource(HasLinks, DummyEntity):
    pass


async def test_without_links() -> None:
    resource = DummyResource()
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wikipedia},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_links_without_wikipedia_links() -> None:
    resource = DummyResource()
    resource.links.append(Link("https://example.com"))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wikipedia},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_without_summaries(mocker: MockerFixture) -> None:
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
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wikipedia},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""
    m_retriever.get_summary.assert_called_once_with("en", "Amsterdam")


async def test_with_summaries_in_irrelevant_locale() -> None:
    wikipedia_url = "https://nl.wikipedia.org/wiki/Amsterdam"
    resource = DummyResource()
    resource.links.append(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wikipedia},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_summary_should_render(mocker: MockerFixture) -> None:
    wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
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
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wikipedia},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert summary.content in actual
        wikipedia_contributors_copyright_notice = WikipediaContributors({})
        assert (
            wikipedia_contributors_copyright_notice.summary.localize(DEFAULT_LOCALIZER)
            in actual
        )
        assert (
            wikipedia_contributors_copyright_notice.url.localize(DEFAULT_LOCALIZER)
            in actual
        )
    m_retriever.get_summary.assert_called_once_with("en", "Amsterdam")
