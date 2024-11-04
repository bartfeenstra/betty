from __future__ import annotations

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.date import Date
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label--citation.html.j2"

    async def test_minimal(self) -> None:
        source = Source()
        citation = Citation(source=source)
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_persistent_id(self) -> None:
        source = Source()
        citation = Citation(id="C0", source=source)
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        source = Source()
        citation = Citation(id="C0", source=source)
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
        async with self.assert_template_file(
            data={
                "entity": citation,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_private_source(self) -> None:
        source = Source(private=True)
        citation = Citation(source=source)
        expected = '<span class="citation-location"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></span>'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_source_author(self) -> None:
        source = Source(author="Bart")
        citation = Citation(source=source)
        expected = (
            f'Bart. <i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
        )
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_source_publisher(self) -> None:
        source = Source(publisher="Bart")
        citation = Citation(source=source)
        expected = (
            f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Bart.'
        )
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_location(self) -> None:
        source = Source()
        citation = Citation(source=source, location="Somewhere")
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Somewhere.'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_citation_context(self) -> None:
        source = Source()
        citation = Citation(id="C0", source=source, location="Somewhere")
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Somewhere.'
        async with self.assert_template_file(
            data={
                "entity": citation,
                "entity_contexts": await EntityContexts.new(citation),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_date(self) -> None:
        source = Source()
        citation = Citation(source=source, date=Date(1970, 1, 1))
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Accessed January 1, 1970.'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_private(self) -> None:
        source = Source()
        citation = Citation(source=source, private=True)
        expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. <span class="citation-location"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></span>'
        async with self.assert_template_file(
            data={
                "entity": citation,
            }
        ) as (actual, _):
            assert actual == expected
