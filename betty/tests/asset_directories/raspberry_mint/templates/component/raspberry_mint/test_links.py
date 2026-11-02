from betty.asset_directories import raspberry_mint
from betty.associations.has_links import HasLinks
from betty.entities.link import Link
from betty.entity import EntityDefinition
from betty.test_utils.conftest import AssertTemplateFile
from betty.test_utils.locale.localizable import dummy_countable_localizable


@EntityDefinition(
    "dummy-has-links",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class DummyEntityWithLinks(HasLinks):
    pass


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "links": [],
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_link_without_locale(
    assert_template_file: AssertTemplateFile,
) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(link_url, label=link_label)
    async with assert_template_file(
        data={
            "links": [link],
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual


async def test_with_link(assert_template_file: AssertTemplateFile) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(link_url, label=link_label)
    async with assert_template_file(
        data={
            "links": [link],
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual
