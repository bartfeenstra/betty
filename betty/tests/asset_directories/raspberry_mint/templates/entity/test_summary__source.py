from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.source import Source
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    async with assert_template_file(
        data={
            "entity": source,
        },
        assets={raspberry_mint},
        template="entity/summary--source.html.j2",
    ) as (actual, _):
        assert actual


async def test_with_contained_by(assert_template_file: AssertTemplateFile) -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    async with assert_template_file(
        data={
            "entity": source,
        },
        assets={raspberry_mint},
        template="entity/summary--source.html.j2",
    ) as (actual, _):
        assert contained_by_source.id in actual
