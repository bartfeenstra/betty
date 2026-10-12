from betty.associations.has_links import HasLinks
from betty.entities.link import Link
from betty.entity import EntityDefinition
from betty.locale import default_locale
from betty.test_utils.conftest import AssertJinja
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-links",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyEntityWithLinks(HasLinks):
    pass


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/links.html.j2", data={"links": []}
    ) as rendered:
        assert rendered == ""


async def test_with_link_without_locale(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link(link_url, label=link_label)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/links.html.j2", data={"links": [link]}
    ) as rendered:
        assert link_url in rendered
        assert link_label in rendered


async def test_with_link(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    link_url = "https://example.com"
    link_label = "An example site"
    link = Link({default_locale: link_url}, label=link_label)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/links.html.j2", data={"links": [link]}
    ) as rendered:
        assert link_url in rendered
        assert link_label in rendered
