from betty.entities.source import Source
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_template_file(
        "entity/source-containment-label.html.j2",
        data={
            "source": source,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected


async def test_with_contained_by(assert_template_file: AssertTemplateFile) -> None:
    contained_by_contained_by_source = Source()
    contained_by_source = Source(contained_by=contained_by_contained_by_source)
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>, <span lang="und" dir="auto">Source {contained_by_source.id}</span>, <span lang="und" dir="auto">Source {contained_by_contained_by_source.id}</span>'
    async with assert_template_file(
        "entity/source-containment-label.html.j2",
        data={
            "source": source,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected


async def test_with_source_context(
    assert_template_file: AssertTemplateFile,
) -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_template_file(
        "entity/source-containment-label.html.j2",
        data={
            "source": source,
            "source_context": contained_by_source,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected
