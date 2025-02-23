from pytest_mock import MockerFixture
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.wikipedia import Wikipedia
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.tests.project.test_load import DummyHasLinks
from betty.wikipedia import Summary


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint, Wikipedia}
    template = "section/wikipedia.html.j2"

    async def test_minimal(self) -> None:
        entity = DummyHasLinks()
        async with self.assert_template_file(
            data={
                "entity": entity,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual

    async def test_with_summary(self, mocker: MockerFixture) -> None:
        summary_content = "Hello, world!"
        m_get_summary = mocker.patch("betty.wikipedia._Retriever.get_summary")
        m_get_summary.return_value = Summary(
            DEFAULT_LOCALE, "Example", "Example", summary_content
        )
        entity = DummyHasLinks(links=[Link("https://en.wikipedia.org/wiki/Example")])
        async with self.assert_template_file(
            data={
                "entity": entity,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert summary_content in actual
