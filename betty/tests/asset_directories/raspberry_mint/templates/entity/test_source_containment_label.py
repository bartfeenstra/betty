from betty.document import Document, EntityContexts
from betty.entities.source import Source
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/source-containment-label.html.j2", data={"source": source}
    ) as rendered:
        assert rendered == expected


async def test_with_contained_by(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    contained_by_contained_by_source = Source()
    contained_by_source = Source(contained_by=contained_by_contained_by_source)
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>, <span lang="und" dir="auto">Source {contained_by_source.id}</span>, <span lang="und" dir="auto">Source {contained_by_contained_by_source.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/source-containment-label.html.j2", data={"source": source}
    ) as rendered:
        assert rendered == expected


async def test_with_contained_by_and_source_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/source-containment-label.html.j2",
        data={
            "source": source,
            "document": Document(entity_contexts=EntityContexts(contained_by_source)),
        },
    ) as rendered:
        assert rendered == expected
