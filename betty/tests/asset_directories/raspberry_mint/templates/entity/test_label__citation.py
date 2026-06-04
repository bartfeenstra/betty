from __future__ import annotations

from typing import TYPE_CHECKING

from betty.document import Document, EntityContexts
from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateFile
from betty.asset_directories.raspberry_mint import raspberry_mint


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(id="C0", source=source)
    expected = f'<a href="/citation/{citation.public_id}/index.html"><i>Unknown</i></a> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(id="C0", source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_template_file(
        data={
            "entity": citation,
            "embedded": True,
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_location(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(source=source, location="Somewhere")
    expected = (
        f'Somewhere <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    )
    async with assert_template_file(
        data={
            "entity": citation,
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citation_context(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(id="C0", source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_template_file(
        data={
            "entity": citation,
            "document": Document(entity_contexts=EntityContexts(citation)),
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_private(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(source=source, privacy=Privacy.PRIVATE)
    expected = f'<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        assets={raspberry_mint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected
