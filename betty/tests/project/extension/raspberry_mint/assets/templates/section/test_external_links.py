from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import CountablePlain, Plain, StaticTranslations
from betty.model import EntityDefinition
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


@EntityDefinition(
    id="dummy-has-links",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class DummyEntityWithLinks(HasLinks):
    pass


async def test_minimal() -> None:
    entity = DummyEntityWithLinks()
    async with assert_template_file(
        data={
            "page_resource": entity,
        },
        extensions={RaspberryMint},
        template="section/external-links.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_link_without_locale() -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(link_url, label=Plain(link_label))
    entity = DummyEntityWithLinks()
    entity.links.add(link)
    async with assert_template_file(
        data={
            "page_resource": entity,
        },
        extensions={RaspberryMint},
        template="section/external-links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual


async def test_with_link() -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(StaticTranslations({DEFAULT_LOCALE: link_url}), label=Plain(link_label))
    entity = DummyEntityWithLinks()
    entity.links.add(link)
    async with assert_template_file(
        data={
            "page_resource": entity,
        },
        extensions={RaspberryMint},
        template="section/external-links.html.j2",
    ) as (actual, _):
        assert link_url in actual
        assert link_label in actual
