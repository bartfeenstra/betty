from betty.plugins.entity.source import Source
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    source = Source()
    async with assert_template_file(
        data={
            "entity": source,
        },
        extensions={RaspberryMint},
        template="entity/summary--source.html.j2",
    ) as (actual, _):
        assert actual


async def test_with_contained_by() -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    async with assert_template_file(
        data={
            "entity": source,
        },
        extensions={RaspberryMint},
        template="entity/summary--source.html.j2",
    ) as (actual, _):
        assert contained_by_source.public_id in actual
