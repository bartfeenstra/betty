from pytest_mock import MockerFixture

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.document import Document
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.project.extension.wiki import Wiki
from betty.test_utils.jinja2 import assert_template_file
from betty.wiki.client import Summary


class DummyResource(HasLinks):
    pass


async def test_without_links() -> None:
    resource = DummyResource()
    async with assert_template_file(
        data={
            "document": Document(resource),
        },
        extensions={Wiki},
        template="wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_links_without_wikipedia_links() -> None:
    resource = DummyResource()
    resource.links.add(Link("https://example.com"))
    async with assert_template_file(
        data={
            "document": Document(resource),
        },
        extensions={Wiki},
        template="wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_without_summaries(mocker: MockerFixture) -> None:
    wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
    m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
    m_get_summary.return_value = None
    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "document": Document(resource),
        },
        extensions={Wiki},
        template="wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""
    m_get_summary.assert_called_once_with("en", "Amsterdam")


async def test_with_summaries_in_irrelevant_locale() -> None:
    wikipedia_url = "https://nl.wikipedia.org/wiki/Amsterdam"
    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "document": Document(resource),
        },
        extensions={Wiki},
        template="wiki/wikipedia-summary.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_summary_should_render(mocker: MockerFixture) -> None:
    wikipedia_url = "https://en.wikipedia.org/wiki/Amsterdam"
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
    m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
    m_get_summary.return_value = summary

    resource = DummyResource()
    resource.links.add(Link(wikipedia_url))
    async with assert_template_file(
        data={
            "document": Document(resource),
        },
        extensions={Wiki},
        template="wiki/wikipedia-summary.html.j2",
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
