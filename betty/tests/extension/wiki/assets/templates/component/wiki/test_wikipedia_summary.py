from pytest_mock import MockerFixture

from betty.ancestry.link import Link
from betty.extension.wiki import Wiki
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.jinja2 import assert_template_file
from betty.wiki.client import Summary


async def test_without_links() -> None:
    async with assert_template_file(
        data={
            "links": [],
        },
        extensions={Wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_links_without_wikipedia_links() -> None:
    async with assert_template_file(
        data={
            "links": [Link("https://example.com")],
        },
        extensions={Wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_without_summaries(mocker: MockerFixture) -> None:
    m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
    m_get_summary.return_value = None
    async with assert_template_file(
        data={
            "links": [Link("https://en.wikipedia.org/wiki/Amsterdam")],
        },
        extensions={Wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""
    m_get_summary.assert_called_once_with("en", "Amsterdam")


async def test_with_summaries_in_irrelevant_locale() -> None:
    async with assert_template_file(
        data={
            "links": [Link("https://nl.wikipedia.org/wiki/Amsterdam")],
        },
        extensions={Wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_summary_should_render(mocker: MockerFixture) -> None:
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
    m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
    m_get_summary.return_value = summary

    async with assert_template_file(
        data={
            "links": [Link("https://en.wikipedia.org/wiki/Amsterdam")],
        },
        extensions={Wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, project):
        extensions = await project.extensions
        wikipedia_contributors_copyright_notice = extensions[
            Wiki
        ]._wikipedia_contributors_copyright_notice
        assert summary.content in actual
        assert (
            wikipedia_contributors_copyright_notice.summary.localize(DEFAULT_LOCALIZER)
            in actual
        )
        assert wikipedia_contributors_copyright_notice.url is not None
        assert (
            wikipedia_contributors_copyright_notice.url.localize(DEFAULT_LOCALIZER)
            in actual
        )
    m_get_summary.assert_called_once_with("en", "Amsterdam")
