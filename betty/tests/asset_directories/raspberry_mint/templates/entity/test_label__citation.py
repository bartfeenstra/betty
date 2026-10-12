from __future__ import annotations

from typing import TYPE_CHECKING

from betty.document import Document, EntityContexts
from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert rendered == expected


async def test_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    citation = Citation(id="my-first-citation", source=source)
    expected = f'<a href="/citation/{citation.id}/index.html"><i>Unknown</i></a> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert rendered == expected


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(id="my-first-citation", source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2", data={"entity": citation, "embedded": True}
    ) as rendered:
        assert rendered == expected


async def test_with_location(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source, location="Somewhere")
    expected = (
        f'Somewhere <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    )
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert rendered == expected


async def test_with_citation_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    citation = Citation(id="my-first-citation", source=source)
    expected = f'<i>Unknown</i> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2",
        data={
            "entity": citation,
            "document": Document(entity_contexts=EntityContexts(citation)),
        },
    ) as rendered:
        assert rendered == expected


async def test_private(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source, privacy=Privacy.PRIVATE)
    expected = f'<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span> <sup>(<span lang="und" dir="auto">Source {source.id}</span>)</sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--citation.html.j2", data={"entity": citation}
    ) as rendered:
        assert rendered == expected
