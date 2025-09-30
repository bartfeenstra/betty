from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Plain, StaticTranslations
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file
from betty.test_utils.model import DummyEntity


class DummyEntityWithLinks(HasLinks, DummyEntity):
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
