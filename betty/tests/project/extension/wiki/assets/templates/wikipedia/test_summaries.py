from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.wiki import Wiki
from betty.test_utils.jinja2 import assert_template_file
from betty.wiki.client import Client, Summary
from betty.wiki.copyright_notice import WikipediaContributors


class DummyResource(HasLinks):
    pass


async def test_without_links() -> None:
    resource = DummyResource()
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wiki},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_links_without_wikipedia_links() -> None:
    resource = DummyResource()
    resource.links.add(Link("https://example.com"))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wiki},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_without_summaries(mocker: MockerFixture) -> None:
    wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
    m_client = mocker.AsyncMock(spec=Client)
    m_client.get_summary.return_value = None

    async def _awaitable_client():
        return m_client  # type: ignore[no-any-return]

    mocker.patch(
        "betty.project.extension.wiki.Wiki.client",
        new_callable=PropertyMock,
        return_value=_awaitable_client(),
    )
    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wiki},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""
    m_client.get_summary.assert_called_once_with("en", "Amsterdam")


async def test_with_summaries_in_irrelevant_locale() -> None:
    wikipedia_url = "https://nl.wikipedia.org/wiki/Amsterdam"
    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wiki},
        template="wikipedia/summaries.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_summary_should_render(mocker: MockerFixture) -> None:
    wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
    m_client = mocker.AsyncMock(spec=Client)
    m_client.get_summary.return_value = summary

    async def _awaitable_client():
        return m_client  # type: ignore[no-any-return]

    mocker.patch(
        "betty.project.extension.wiki.Wiki.client",
        new_callable=PropertyMock,
        return_value=_awaitable_client(),
    )
    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "resource": resource,
        },
        extensions={Wiki},
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
    m_client.get_summary.assert_called_once_with("en", "Amsterdam")
