from pytest_mock import MockerFixture

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import CountablePlain
from betty.model import EntityPlugin
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.wiki import Wiki
from betty.resource import new_context
from betty.test_utils.jinja2 import assert_template_file
from betty.wiki.client import Summary


@EntityPlugin(
    id="dummy-has-links",
    label="",
    label_plural="",
    label_countable=CountablePlain("", ""),
)
class DummyHasLinks(HasLinks):
    pass


async def test_minimal() -> None:
    resource = DummyHasLinks()
    async with assert_template_file(
        data={
            "resource": new_context(resource),
        },
        extensions={RaspberryMint, Wiki},
        template="section/wikipedia.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_summary(mocker: MockerFixture) -> None:
    summary_content = "Hello, world!"
    m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
    m_get_summary.return_value = Summary(
        DEFAULT_LOCALE, "Example", "Example", summary_content
    )
    resource = DummyHasLinks(links=[Link("https://en.wikipedia.org/wiki/Example")])
    async with assert_template_file(
        data={
            "resource": new_context(resource),
        },
        extensions={RaspberryMint, Wiki},
        template="section/wikipedia.html.j2",
    ) as (actual, _):
        assert summary_content in actual
