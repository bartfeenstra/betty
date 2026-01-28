from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.extension.raspberry_mint import RaspberryMint
from betty.privacy import Privacy
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    source = Source()
    citation = Citation(source=source)
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/summary--citation.html.j2",
    ) as (actual, _):
        assert source.public_id in actual


async def test_with_private_source() -> None:
    source = Source(privacy=Privacy.PRIVATE)
    citation = Citation(source=source)
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/summary--citation.html.j2",
    ) as (actual, _):
        assert source.id not in actual
