from betty.ancestry.has_links import HasLinks
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.model import EntityDefinition
from betty.plugins.entity.link import Link
from betty.plugins.extension.raspberry_mint import RaspberryMint
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
        extensions={RaspberryMint},
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
        extensions={RaspberryMint},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual


async def test_with_link(assert_template_file: AssertTemplateFile) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(StaticTranslations({DEFAULT_LOCALE_TAG: link_url}), label=link_label)
    async with assert_template_file(
        data={
            "links": [link],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual
