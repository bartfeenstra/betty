from betty.entity import EntityDefinition
from betty.entity.has_links import HasLinks
from betty.locale import DEFAULT_LOCALE
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.link import Link
from betty.test_utils.conftest import AssertTemplateFile
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-links",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyEntityWithLinks(HasLinks):
    pass


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "links": [],
        },
        assets={RASPBERRY_MINT},
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
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual


async def test_with_link(assert_template_file: AssertTemplateFile) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(
        {DEFAULT_LOCALE: link_url},  # ty:ignore[invalid-argument-type]
        label=link_label,
    )
    async with assert_template_file(
        data={
            "links": [link],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual
