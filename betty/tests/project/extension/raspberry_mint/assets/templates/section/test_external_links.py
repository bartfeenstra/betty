from betty.ancestry.link import HasLinks, Link
from betty.locale import DEFAULT_LOCALE
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.test_utils.model import DummyEntity


class DummyEntityWithLinks(HasLinks, DummyEntity):
    pass


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "section/external-links.html.j2"

    async def test_minimal(self) -> None:
        entity = DummyEntityWithLinks()
        async with self.assert_template_file(
            data={
                "page_resource": entity,
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_link_without_locale(self) -> None:
        link_url = "https://example.com"
        link_label = "An example site"
        link = Link(link_url, label=link_label)
        entity = DummyEntityWithLinks()
        entity.links.append(link)
        async with self.assert_template_file(
            data={
                "page_resource": entity,
            }
        ) as (actual, _):
            assert link_url in actual
            assert link_label in actual

    async def test_with_link_with_matching_locale(self) -> None:
        link_url = "https://example.com"
        link_label = "An example site"
        link = Link(link_url, label=link_label, locale=DEFAULT_LOCALE)
        entity = DummyEntityWithLinks()
        entity.links.append(link)
        async with self.assert_template_file(
            data={
                "page_resource": entity,
            }
        ) as (actual, _):
            assert link_url in actual
            assert link_label in actual

    async def test_with_link_without_matching_locale(self) -> None:
        link_url = "https://example.com"
        link_label = "An example site"
        link = Link(link_url, label=link_label, locale="nl")
        entity = DummyEntityWithLinks()
        entity.links.append(link)
        async with self.assert_template_file(
            data={
                "page_resource": entity,
            }
        ) as (actual, _):
            assert link_url not in actual
            assert link_label not in actual
